import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate

async def get_role(db: AsyncSession, role_id: uuid.UUID) -> Optional[Role]:
    result = await db.execute(select(Role).where(Role.id == role_id))
    return result.scalar_one_or_none()

async def list_roles(db: AsyncSession, is_active: Optional[bool] = None) -> List[Role]:
    query = select(Role)
    if is_active is not None:
        query = query.where(Role.is_active == is_active)
    result = await db.execute(query.order_by(Role.name))
    return list(result.scalars().all())

async def create_role(db: AsyncSession, data: RoleCreate) -> Role:
    role = Role(
        name=data.name,
        permissions=data.permissions,
        is_active=data.is_active
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role

async def update_role(db: AsyncSession, role_id: uuid.UUID, data: RoleUpdate) -> Optional[Role]:
    role = await get_role(db, role_id)
    if not role:
        return None
    
    if data.name is not None:
        role.name = data.name
    if data.permissions is not None:
        role.permissions = data.permissions
    if data.is_active is not None:
        role.is_active = data.is_active
        
    await db.commit()
    await db.refresh(role)
    return role
