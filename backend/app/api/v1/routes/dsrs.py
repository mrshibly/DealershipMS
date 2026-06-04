"""
DSR routes — CRUD.
"""
import uuid
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.dsr import DSRCreate, DSRRead, DSRUpdate
from app.services import dsr_service

router = APIRouter(prefix="/dsrs", tags=["dsrs"])


@router.get("", response_model=PaginatedResponse[DSRRead])
async def list_dsrs(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    route_id: uuid.UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dsrs", "view")),
):
    dsrs, total = await dsr_service.list_dsrs(
        db, page=page, per_page=per_page, search=search, route_id=route_id, is_active=is_active
    )
    return PaginatedResponse(
        data=dsrs, total=total, page=page,
        per_page=per_page, pages=ceil(total / per_page) if total else 0,
    )


@router.get("/{dsr_id}", response_model=SuccessResponse[DSRRead])
async def get_dsr(
    dsr_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dsrs", "view")),
):
    dsr = await dsr_service.get_dsr(db, dsr_id)
    if not dsr:
        raise HTTPException(status_code=404, detail="DSR not found")
    return SuccessResponse(data=dsr)


@router.post("", response_model=SuccessResponse[DSRRead], status_code=201)
async def create_dsr(
    body: DSRCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("dsrs", "create")),
):
    try:
        dsr = await dsr_service.create_dsr(db, body, current_user.id)
        return SuccessResponse(data=dsr, message="DSR created")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{dsr_id}", response_model=SuccessResponse[DSRRead])
async def update_dsr(
    dsr_id: uuid.UUID = Path(...),
    body: DSRUpdate = ...,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dsrs", "update")),
):
    try:
        dsr = await dsr_service.update_dsr(db, dsr_id, body)
        if not dsr:
            raise HTTPException(status_code=404, detail="DSR not found")
        return SuccessResponse(data=dsr, message="DSR updated")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{dsr_id}", response_model=SuccessResponse[dict])
async def delete_dsr(
    dsr_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dsrs", "delete")),
):
    deleted = await dsr_service.delete_dsr(db, dsr_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="DSR not found")
    return SuccessResponse(data={}, message="DSR deleted")
