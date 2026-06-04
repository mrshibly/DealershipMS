"""
Inventory routes — stock levels, opening stock, adjustments, movement history.
"""
import uuid
from datetime import date
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.inventory import (
    OpeningStockCreate, StockAdjustmentCreate,
    StockLevelRead, StockMovementRead,
)
from app.services import inventory_service, product_service

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/stock", response_model=PaginatedResponse[StockLevelRead])
async def list_stock(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    low_stock_only: bool = Query(default=False),
    category_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("inventory", "view")),
):
    stock, total = await inventory_service.list_stock(
        db, page=page, per_page=per_page,
        low_stock_only=low_stock_only, category_id=category_id,
    )
    return PaginatedResponse(
        data=stock, total=total, page=page,
        per_page=per_page, pages=ceil(total / per_page) if total else 0,
    )


@router.post("/opening-stock", response_model=SuccessResponse[dict], status_code=201)
async def add_opening_stock(
    body: OpeningStockCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("inventory", "create")),
):
    # Validate product exists
    product = await product_service.get_product(db, body.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    try:
        movement = await inventory_service.add_opening_stock(db, body, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return SuccessResponse(
        data={"movement_id": str(movement.id), "qty_pieces": movement.qty_pieces},
        message="Opening stock added",
    )


@router.post("/adjustments", response_model=SuccessResponse[dict], status_code=201)
async def add_adjustment(
    body: StockAdjustmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("inventory", "create")),
):
    product = await product_service.get_product(db, body.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    try:
        movement = await inventory_service.add_stock_adjustment(db, body, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return SuccessResponse(
        data={"movement_id": str(movement.id), "qty_pieces": movement.qty_pieces},
        message="Adjustment recorded",
    )


@router.get(
    "/movements/{product_id}",
    response_model=PaginatedResponse[StockMovementRead],
)
async def get_movements(
    product_id: uuid.UUID = Path(...),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=30, ge=1, le=100),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("inventory", "view")),
):
    movements, total = await inventory_service.get_product_movements(
        db, product_id, page=page, per_page=per_page,
        date_from=date_from, date_to=date_to,
    )
    data = [
        {
            "id": m.id,
            "product_id": m.product_id,
            "product_name_en": m.product.name_en if m.product else "",
            "movement_type": m.movement_type.value if hasattr(m.movement_type, "value") else m.movement_type,
            "qty_pieces": m.qty_pieces,
            "unit_price": m.unit_price,
            "movement_date": m.movement_date,
            "notes": m.notes,
            "created_at": m.created_at,
        }
        for m in movements
    ]
    return PaginatedResponse(
        data=data, total=total, page=page,
        per_page=per_page, pages=ceil(total / per_page) if total else 0,
    )
