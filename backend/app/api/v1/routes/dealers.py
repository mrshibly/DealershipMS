"""
Dealer routes — CRUD.
"""
import uuid
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.dealer import DealerCreate, DealerRead, DealerUpdate
from app.schemas.shop import ShopRead
from app.services import dealer_service, shop_service

router = APIRouter(prefix="/dealers", tags=["dealers"])


@router.get("", response_model=PaginatedResponse[DealerRead])
async def list_dealers(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    route_id: uuid.UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dealers", "view")),
):
    dealers, total = await dealer_service.list_dealers(
        db, page=page, per_page=per_page, search=search, route_id=route_id, is_active=is_active
    )
    return PaginatedResponse(
        data=dealers, total=total, page=page,
        per_page=per_page, pages=ceil(total / per_page) if total else 0,
    )


@router.get("/{dealer_id}", response_model=SuccessResponse[DealerRead])
async def get_dealer(
    dealer_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dealers", "view")),
):
    dealer = await dealer_service.get_dealer(db, dealer_id)
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
    return SuccessResponse(data=dealer)


@router.post("", response_model=SuccessResponse[DealerRead], status_code=201)
async def create_dealer(
    body: DealerCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("dealers", "create")),
):
    try:
        dealer = await dealer_service.create_dealer(db, body, current_user.id)
        return SuccessResponse(data=dealer, message="Dealer created")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{dealer_id}", response_model=SuccessResponse[DealerRead])
async def update_dealer(
    dealer_id: uuid.UUID = Path(...),
    body: DealerUpdate = ...,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dealers", "update")),
):
    try:
        dealer = await dealer_service.update_dealer(db, dealer_id, body)
        if not dealer:
            raise HTTPException(status_code=404, detail="Dealer not found")
        return SuccessResponse(data=dealer, message="Dealer updated")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{dealer_id}", response_model=SuccessResponse[dict])
async def delete_dealer(
    dealer_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dealers", "delete")),
):
    deleted = await dealer_service.delete_dealer(db, dealer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Dealer not found")
    return SuccessResponse(data={}, message="Dealer deleted")


@router.get("/{dealer_id}/shops", response_model=SuccessResponse[list[ShopRead]])
async def list_dealer_shops(
    dealer_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dealers", "view")),
):
    # Verify dealer exists
    dealer = await dealer_service.get_dealer(db, dealer_id)
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
    shops = await shop_service.list_shops_by_dealer(db, dealer_id)
    return SuccessResponse(data=shops)
