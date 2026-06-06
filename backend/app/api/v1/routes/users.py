import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import SuccessResponse
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=SuccessResponse[List[UserRead]])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("users", "view")),
):
    users = await user_service.list_users(db)
    
    enriched = []
    for u in users:
        ur = UserRead.model_validate(u)
        ur.role_name = u.role.name if u.role else None
        enriched.append(ur)
        
    return SuccessResponse(data=enriched)

@router.get("/{user_id}", response_model=SuccessResponse[UserRead])
async def get_user(
    user_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("users", "view")),
):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    ur = UserRead.model_validate(user)
    ur.role_name = user.role.name if user.role else None
    return SuccessResponse(data=ur)

@router.post("", response_model=SuccessResponse[UserRead], status_code=201)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("users", "create")),
):
    user = await user_service.create_user(db, body)
    
    ur = UserRead.model_validate(user)
    ur.role_name = user.role.name if user.role else None
    
    return SuccessResponse(data=ur, message="User created")

@router.put("/{user_id}", response_model=SuccessResponse[UserRead])
async def update_user(
    user_id: uuid.UUID = Path(...),
    body: UserUpdate = ...,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("users", "update")),
):
    user = await user_service.update_user(db, user_id, body)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    ur = UserRead.model_validate(user)
    ur.role_name = user.role.name if user.role else None
        
    return SuccessResponse(data=ur, message="User updated")

@router.delete("/{user_id}", response_model=SuccessResponse[dict])
async def delete_user(
    user_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("users", "delete")),
):
    deleted = await user_service.delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return SuccessResponse(data={}, message="User deleted")
