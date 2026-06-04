"""
Auth business logic service.
All auth operations live here — route handlers are thin.
"""
from datetime import datetime, timezone

import redis.asyncio as aioredis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import AccessTokenResponse, TokenResponse

settings = get_settings()


async def _get_redis() -> aioredis.Redis:
    return aioredis.from_url(settings.redis_url, decode_responses=True)


BLACKLIST_PREFIX = "token:blacklist:"


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Return User if credentials valid, else None."""
    result = await db.execute(
        select(User).where(
            User.email == email,
            User.is_active.is_(True),
            User.is_deleted.is_(False),
        )
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


async def login(db: AsyncSession, email: str, password: str) -> TokenResponse:
    """
    Authenticate user and return JWT token pair.
    Raises ValueError on invalid credentials.
    """
    user = await authenticate_user(db, email, password)
    if user is None:
        raise ValueError("Invalid email or password")

    # Update last_login
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(last_login=datetime.now(timezone.utc))
    )
    await db.commit()

    access_token = create_access_token(
        subject=user.id,
        extra={"role": str(user.role_id), "email": user.email},
    )
    refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


async def refresh_access_token(refresh_token: str) -> AccessTokenResponse:
    """
    Issue a new access token given a valid refresh token.
    Raises ValueError if token is invalid or blacklisted.
    """
    payload = decode_token(refresh_token)  # raises HTTPException if invalid

    if payload.get("type") != TOKEN_TYPE_REFRESH:
        raise ValueError("Not a refresh token")

    # Check blacklist
    redis_client = await _get_redis()
    is_blacklisted = await redis_client.exists(f"{BLACKLIST_PREFIX}{refresh_token}")
    await redis_client.aclose()

    if is_blacklisted:
        raise ValueError("Token has been revoked")

    user_id = payload["sub"]
    new_access = create_access_token(subject=user_id)

    return AccessTokenResponse(
        access_token=new_access,
        expires_in=settings.access_token_expire_minutes * 60,
    )


async def logout(access_token: str, refresh_token: str | None = None) -> None:
    """
    Blacklist both tokens in Redis with TTL matching their expiry.
    """
    redis_client = await _get_redis()
    try:
        # Blacklist access token
        payload = decode_token(access_token)
        exp = payload.get("exp", 0)
        ttl = max(0, int(exp - datetime.now(timezone.utc).timestamp()))
        if ttl > 0:
            await redis_client.setex(f"{BLACKLIST_PREFIX}{access_token}", ttl, "1")

        # Blacklist refresh token if provided
        if refresh_token:
            try:
                r_payload = decode_token(refresh_token)
                r_exp = r_payload.get("exp", 0)
                r_ttl = max(0, int(r_exp - datetime.now(timezone.utc).timestamp()))
                if r_ttl > 0:
                    await redis_client.setex(f"{BLACKLIST_PREFIX}{refresh_token}", r_ttl, "1")
            except Exception:
                pass  # If refresh token invalid, ignore
    finally:
        await redis_client.aclose()
