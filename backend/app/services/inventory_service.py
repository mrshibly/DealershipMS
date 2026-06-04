"""
Inventory business logic service.
Stock is ALWAYS computed from stock_movements — never stored on the product.
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.stock_movement import (
    INWARD_TYPES, OUTWARD_TYPES,
    MovementType, StockMovement,
)
from app.schemas.inventory import OpeningStockCreate, StockAdjustmentCreate


ADJUSTMENT_ALLOWED = {
    MovementType.OPENING_STOCK,
    MovementType.ADJUSTMENT_IN,
    MovementType.ADJUSTMENT_OUT,
    MovementType.DAMAGE,
    MovementType.FREE_GIVEN,
}


async def get_stock_level(db: AsyncSession, product: Product) -> dict[str, Any]:
    """Compute stock for a single product."""
    inward = await db.execute(
        select(func.coalesce(func.sum(StockMovement.qty_pieces), 0)).where(
            StockMovement.product_id == product.id,
            StockMovement.movement_type.in_([t.value for t in INWARD_TYPES]),
            StockMovement.is_approved.is_(True),
        )
    )
    outward = await db.execute(
        select(func.coalesce(func.sum(StockMovement.qty_pieces), 0)).where(
            StockMovement.product_id == product.id,
            StockMovement.movement_type.in_([t.value for t in OUTWARD_TYPES]),
            StockMovement.is_approved.is_(True),
        )
    )
    qty_pcs: int = max(0, (inward.scalar() or 0) - (outward.scalar() or 0))
    ppc = product.pcs_per_carton or 1
    cartons = qty_pcs // ppc
    remaining = qty_pcs % ppc

    return {
        "product_id": product.id,
        "product_name_en": product.name_en,
        "product_name_bn": product.name_bn,
        "sku": product.sku,
        "barcode": product.barcode,
        "pcs_per_carton": product.pcs_per_carton,
        "unit": product.unit,
        "qty_pieces": qty_pcs,
        "qty_cartons": cartons,
        "remaining_pcs": remaining,
        "buy_value": Decimal(str(qty_pcs)) * product.buy_price,
        "sell_value": Decimal(str(qty_pcs)) * product.sell_price,
        "low_stock_threshold": product.low_stock_threshold,
        "is_low_stock": qty_pcs <= product.low_stock_threshold,
        "category_name": product.category.name if product.category else None,
    }


async def list_stock(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 50,
    low_stock_only: bool = False,
    category_id: uuid.UUID | None = None,
) -> tuple[list[dict], int]:
    query = (
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.is_deleted.is_(False), Product.is_active.is_(True))
    )
    if category_id:
        query = query.where(Product.category_id == category_id)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar() or 0

    query = query.order_by(Product.name_en).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    products = result.scalars().all()

    stock_list = []
    for p in products:
        level = await get_stock_level(db, p)
        if low_stock_only and not level["is_low_stock"]:
            continue
        stock_list.append(level)

    return stock_list, total


async def add_opening_stock(
    db: AsyncSession,
    data: OpeningStockCreate,
    created_by: uuid.UUID,
) -> StockMovement:
    """
    Create opening stock entry. Idempotency: check if product already has
    an OPENING_STOCK movement — raise if so.
    """
    existing = await db.execute(
        select(StockMovement).where(
            StockMovement.product_id == data.product_id,
            StockMovement.movement_type == MovementType.OPENING_STOCK,
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("Opening stock already entered for this product. Use an adjustment instead.")

    movement = StockMovement(
        product_id=data.product_id,
        movement_type=MovementType.OPENING_STOCK,
        qty_pieces=data.qty_pieces,
        unit_price=data.unit_price,
        movement_date=data.movement_date,
        notes=data.notes,
        is_approved=True,
        created_by=created_by,
    )
    db.add(movement)
    await db.commit()
    await db.refresh(movement)
    return movement


async def add_stock_adjustment(
    db: AsyncSession,
    data: StockAdjustmentCreate,
    created_by: uuid.UUID,
) -> StockMovement:
    """
    Manual stock adjustment. Only ADJUSTMENT_* and DAMAGE / FREE_GIVEN types allowed.
    ADJUSTMENT_OUT adjustments that would bring stock negative raise ValueError.
    """
    mv_type = MovementType(data.movement_type)
    if mv_type not in ADJUSTMENT_ALLOWED:
        raise ValueError(
            f"movement_type must be one of: {', '.join(t.value for t in ADJUSTMENT_ALLOWED)}"
        )

    # Guard: prevent negative stock on outward adjustments
    if mv_type in OUTWARD_TYPES:
        product_result = await db.execute(select(Product).where(Product.id == data.product_id))
        product = product_result.scalar_one_or_none()
        if product:
            level = await get_stock_level(db, product)
            if data.qty_pieces > level["qty_pieces"]:
                raise ValueError(
                    f"Insufficient stock. Available: {level['qty_pieces']} pcs, "
                    f"requested: {data.qty_pieces} pcs"
                )

    movement = StockMovement(
        product_id=data.product_id,
        movement_type=mv_type,
        qty_pieces=data.qty_pieces,
        unit_price=data.unit_price,
        movement_date=data.movement_date,
        notes=data.notes,
        requires_approval=mv_type == MovementType.ADJUSTMENT_OUT,
        is_approved=True,  # TODO: approval workflow in Sprint 7
        created_by=created_by,
    )
    db.add(movement)
    await db.commit()
    await db.refresh(movement)
    return movement


async def get_product_movements(
    db: AsyncSession,
    product_id: uuid.UUID,
    page: int = 1,
    per_page: int = 30,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[StockMovement], int]:
    query = (
        select(StockMovement)
        .options(selectinload(StockMovement.product))
        .where(StockMovement.product_id == product_id)
    )
    if date_from:
        query = query.where(StockMovement.movement_date >= date_from)
    if date_to:
        query = query.where(StockMovement.movement_date <= date_to)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar() or 0

    query = (
        query.order_by(StockMovement.movement_date.desc(), StockMovement.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    return list(result.scalars().all()), total
