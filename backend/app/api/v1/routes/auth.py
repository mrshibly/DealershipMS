"""
Auth route handlers — thin wrappers around auth_service.
Public routes: /auth/login, /auth/refresh
Protected: /auth/logout (requires JWT)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.common import SuccessResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer()


@router.post(
    "/login",
    response_model=SuccessResponse[TokenResponse],
    summary="Login with email and password",
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[TokenResponse]:
    try:
        token_data = await auth_service.login(db, body.email, body.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    return SuccessResponse(data=token_data, message="Login successful")


@router.post(
    "/refresh",
    response_model=SuccessResponse[AccessTokenResponse],
    summary="Get a new access token using refresh token",
)
async def refresh(body: RefreshRequest) -> SuccessResponse[AccessTokenResponse]:
    try:
        token_data = await auth_service.refresh_access_token(body.refresh_token)
    except (ValueError, Exception) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    return SuccessResponse(data=token_data, message="Token refreshed")


@router.post(
    "/logout",
    response_model=SuccessResponse[dict],
    summary="Logout and invalidate tokens",
)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    current_user=Depends(get_current_user),
) -> SuccessResponse[dict]:
    await auth_service.logout(access_token=credentials.credentials)
    return SuccessResponse(data={}, message="Logged out successfully")
