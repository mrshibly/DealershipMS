from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import SuccessResponse
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/snapshot", response_model=SuccessResponse[dict[str, Any]])
async def get_dashboard_snapshot(
    target_date: date = Query(default_factory=date.today),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("reports", "view")),
):
    data = await dashboard_service.get_daily_snapshot(db, target_date)
    return SuccessResponse(data=data)

@router.get("/analytics", response_model=SuccessResponse[list[dict[str, Any]]])
async def get_dashboard_analytics(
    period: str = Query(default="monthly", pattern="^(monthly|yearly)$"),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("reports", "view")),
):
    data = await dashboard_service.get_analytics(db, period=period)
    return SuccessResponse(data=data)
