"""
Route routes — CRUD.
"""
import uuid
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.route import RouteCreate, RouteRead, RouteUpdate
from app.services import route_service

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=PaginatedResponse[RouteRead])
async def list_routes(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("routes", "view")),
):
    routes, total = await route_service.list_routes(
        db, page=page, per_page=per_page, search=search, is_active=is_active
    )
    return PaginatedResponse(
        data=routes, total=total, page=page,
        per_page=per_page, pages=ceil(total / per_page) if total else 0,
    )


@router.get("/{route_id}", response_model=SuccessResponse[RouteRead])
async def get_route(
    route_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("routes", "view")),
):
    route = await route_service.get_route(db, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return SuccessResponse(data=route)


@router.post("", response_model=SuccessResponse[RouteRead], status_code=201)
async def create_route(
    body: RouteCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("routes", "create")),
):
    route = await route_service.create_route(db, body, current_user.id)
    return SuccessResponse(data=route, message="Route created")


@router.put("/{route_id}", response_model=SuccessResponse[RouteRead])
async def update_route(
    route_id: uuid.UUID = Path(...),
    body: RouteUpdate = ...,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("routes", "update")),
):
    route = await route_service.update_route(db, route_id, body)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return SuccessResponse(data=route, message="Route updated")


@router.delete("/{route_id}", response_model=SuccessResponse[dict])
async def delete_route(
    route_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("routes", "delete")),
):
    deleted = await route_service.delete_route(db, route_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Route not found")
    return SuccessResponse(data={}, message="Route deleted")
