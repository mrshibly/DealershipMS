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
    date_from: date = Query(None),
    date_to: date = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("reports", "view")),
):
    if not date_from:
        # Default to start of current month
        date_from = date.today().replace(day=1)
    if not date_to:
        date_to = date.today()
    data = await dashboard_service.get_daily_snapshot(db, date_from, date_to)
    return SuccessResponse(data=data)

@router.get("/analytics", response_model=SuccessResponse[list[dict[str, Any]]])
async def get_dashboard_analytics(
    period: str = Query(default="monthly", pattern="^(monthly|yearly)$"),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("reports", "view")),
):
    data = await dashboard_service.get_analytics(db, period=period)
    return SuccessResponse(data=data)
