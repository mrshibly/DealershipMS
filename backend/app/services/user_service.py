import uuid
from typing import List, Optional

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def get_user(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id, User.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()

async def list_users(db: AsyncSession, is_active: Optional[bool] = None) -> List[User]:
    query = select(User).options(selectinload(User.role)).where(User.is_deleted.is_(False))
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    result = await db.execute(query.order_by(User.name))
    return list(result.scalars().all())

async def create_user(db: AsyncSession, data: UserCreate) -> User:
    # Check email duplicate (simplified, actual should handle constraint)
    hashed_password = get_password_hash(data.password)
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hashed_password,
        role_id=data.role_id,
        phone=data.phone,
        language=data.language
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return await get_user(db, user.id)

async def update_user(db: AsyncSession, user_id: uuid.UUID, data: UserUpdate) -> Optional[User]:
    user = await get_user(db, user_id)
    if not user:
        return None
    
    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        user.email = data.email
    if data.role_id is not None:
        user.role_id = data.role_id
    if data.phone is not None:
        user.phone = data.phone
    if data.language is not None:
        user.language = data.language
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.password:
        user.password_hash = get_password_hash(data.password)
        
    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> bool:
    user = await get_user(db, user_id)
    if not user:
        return False
    user.is_deleted = True
    user.is_active = False
    await db.commit()
    return True
