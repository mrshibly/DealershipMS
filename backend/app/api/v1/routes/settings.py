from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import SuccessResponse
from app.services import setting_service

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("", response_model=SuccessResponse[Dict[str, str]])
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("settings", "view")),
):
    settings = await setting_service.get_all_settings(db)
    return SuccessResponse(data=settings)

@router.put("", response_model=SuccessResponse[Dict[str, str]])
async def update_settings(
    settings_data: Dict[str, str],
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("settings", "update")),
):
    updated = await setting_service.update_settings(db, settings_data)
    return SuccessResponse(data=updated, message="Settings updated successfully")
