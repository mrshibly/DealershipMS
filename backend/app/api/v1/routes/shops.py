"""
Shop routes — CRUD.
"""
import uuid
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.shop import ShopCreate, ShopRead, ShopUpdate
from app.services import shop_service

router = APIRouter(prefix="/shops", tags=["shops"])


@router.get("", response_model=PaginatedResponse[ShopRead])
async def list_shops(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    dealer_id: uuid.UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("shops", "view")),
):
    shops, total = await shop_service.list_shops(
        db, page=page, per_page=per_page, search=search, dealer_id=dealer_id, is_active=is_active
    )
    return PaginatedResponse(
        data=shops, total=total, page=page,
        per_page=per_page, pages=ceil(total / per_page) if total else 0,
    )


@router.get("/{shop_id}", response_model=SuccessResponse[ShopRead])
async def get_shop(
    shop_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("shops", "view")),
):
    shop = await shop_service.get_shop(db, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return SuccessResponse(data=shop)


@router.post("", response_model=SuccessResponse[ShopRead], status_code=201)
async def create_shop(
    body: ShopCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("shops", "create")),
):
    shop = await shop_service.create_shop(db, body, current_user.id)
    return SuccessResponse(data=shop, message="Shop created")


@router.put("/{shop_id}", response_model=SuccessResponse[ShopRead])
async def update_shop(
    shop_id: uuid.UUID = Path(...),
    body: ShopUpdate = ...,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("shops", "update")),
):
    shop = await shop_service.update_shop(db, shop_id, body)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return SuccessResponse(data=shop, message="Shop updated")


@router.delete("/{shop_id}", response_model=SuccessResponse[dict])
async def delete_shop(
    shop_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("shops", "delete")),
):
    deleted = await shop_service.delete_shop(db, shop_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Shop not found")
    return SuccessResponse(data={}, message="Shop deleted")
