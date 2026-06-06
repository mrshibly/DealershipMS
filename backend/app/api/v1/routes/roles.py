import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import SuccessResponse
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.services import role_service

router = APIRouter(prefix="/roles", tags=["roles"])

@router.get("", response_model=SuccessResponse[List[RoleRead]])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("roles", "view")),
):
    roles = await role_service.list_roles(db)
    return SuccessResponse(data=roles)

@router.get("/{role_id}", response_model=SuccessResponse[RoleRead])
async def get_role(
    role_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("roles", "view")),
):
    role = await role_service.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return SuccessResponse(data=role)

@router.post("", response_model=SuccessResponse[RoleRead], status_code=201)
async def create_role(
    body: RoleCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("roles", "create")),
):
    role = await role_service.create_role(db, body)
    return SuccessResponse(data=role, message="Role created")

@router.put("/{role_id}", response_model=SuccessResponse[RoleRead])
async def update_role(
    role_id: uuid.UUID = Path(...),
    body: RoleUpdate = ...,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("roles", "update")),
):
    role = await role_service.update_role(db, role_id, body)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return SuccessResponse(data=role, message="Role updated")
