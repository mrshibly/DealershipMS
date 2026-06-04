"""
Product business logic service.
All DB queries here — route handlers are thin.
"""
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.product import Product
from app.models.stock_movement import INWARD_TYPES, OUTWARD_TYPES, StockMovement
from app.schemas.product import ProductCreate, ProductUpdate
from app.utils.barcode import generate_sku


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _compute_stock(db: AsyncSession, product_id: uuid.UUID) -> int:
    """Return current stock in pieces by summing stock_movements."""
    inward_result = await db.execute(
        select(func.coalesce(func.sum(StockMovement.qty_pieces), 0)).where(
            StockMovement.product_id == product_id,
            StockMovement.movement_type.in_([t.value for t in INWARD_TYPES]),
            StockMovement.is_approved.is_(True),
        )
    )
    outward_result = await db.execute(
        select(func.coalesce(func.sum(StockMovement.qty_pieces), 0)).where(
            StockMovement.product_id == product_id,
            StockMovement.movement_type.in_([t.value for t in OUTWARD_TYPES]),
            StockMovement.is_approved.is_(True),
        )
    )
    inward: int = inward_result.scalar() or 0
    outward: int = outward_result.scalar() or 0
    return max(0, inward - outward)


async def _enrich_product(db: AsyncSession, product: Product) -> dict[str, Any]:
    """Add computed stock fields to product dict."""
    stock_pcs = await _compute_stock(db, product.id)
    pcs_per_carton = product.pcs_per_carton or 1
    cartons = stock_pcs // pcs_per_carton
    category_name = product.category.name if product.category else None
    return {
        **{c.name: getattr(product, c.name) for c in product.__table__.columns},
        "stock_qty_pieces": stock_pcs,
        "stock_qty_cartons": cartons,
        "is_low_stock": stock_pcs <= product.low_stock_threshold,
        "category_name": category_name,
    }


# ── Category CRUD ─────────────────────────────────────────────────────────────

async def list_categories(db: AsyncSession) -> list[Category]:
    result = await db.execute(
        select(Category).where(Category.is_deleted.is_(False)).order_by(Category.name)
    )
    return list(result.scalars().all())


async def create_category(db: AsyncSession, data: dict, created_by: uuid.UUID) -> Category:
    cat = Category(**data, created_by=created_by)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


# ── Product CRUD ──────────────────────────────────────────────────────────────

async def get_product(db: AsyncSession, product_id: uuid.UUID) -> Product | None:
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.id == product_id, Product.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


async def get_product_by_barcode(db: AsyncSession, barcode: str) -> Product | None:
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.barcode == barcode, Product.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


async def list_products(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    search: str | None = None,
    category_id: uuid.UUID | None = None,
    is_active: bool | None = None,
) -> tuple[list[dict], int]:
    query = (
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.is_deleted.is_(False))
    )
    if search:
        pattern = f"%{search}%"
        from sqlalchemy import or_
        query = query.where(
            or_(
                Product.name_en.ilike(pattern),
                Product.name_bn.ilike(pattern),
                Product.sku.ilike(pattern),
                Product.barcode.ilike(pattern),
            )
        )
    if category_id:
        query = query.where(Product.category_id == category_id)
    if is_active is not None:
        query = query.where(Product.is_active.is_(is_active))

    # Total count
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar() or 0

    # Paginated results
    query = query.order_by(Product.name_en).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    products = result.scalars().all()

    enriched = []
    for p in products:
        enriched.append(await _enrich_product(db, p))
    return enriched, total


async def create_product(
    db: AsyncSession, data: ProductCreate, created_by: uuid.UUID
) -> dict[str, Any]:
    # Auto-generate SKU if not provided
    sku = data.sku
    if not sku:
        # Generate and ensure uniqueness
        for _ in range(10):
            candidate = generate_sku()
            existing = await db.execute(select(Product).where(Product.sku == candidate))
            if not existing.scalar_one_or_none():
                sku = candidate
                break
        else:
            raise ValueError("Could not generate unique SKU, please provide one")

    # Validate SKU uniqueness
    existing = await db.execute(
        select(Product).where(Product.sku == sku, Product.is_deleted.is_(False))
    )
    if existing.scalar_one_or_none():
        raise ValueError(f"SKU '{sku}' already exists")

    # Auto-generate barcode (EAN-13 compatible Code128 string)
    import secrets
    barcode_val = f"BD{secrets.randbelow(10**11):011d}"

    product = Product(
        **data.model_dump(exclude={"sku"}),
        sku=sku,
        barcode=barcode_val,
        created_by=created_by,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product, ["category"])
    return await _enrich_product(db, product)


async def update_product(
    db: AsyncSession, product_id: uuid.UUID, data: ProductUpdate, updated_by: uuid.UUID
) -> dict[str, Any] | None:
    product = await get_product(db, product_id)
    if not product:
        return None
    update_data = data.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    await db.commit()
    await db.refresh(product, ["category"])
    return await _enrich_product(db, product)


async def delete_product(db: AsyncSession, product_id: uuid.UUID) -> bool:
    """Soft delete — sets is_deleted=True."""
    product = await get_product(db, product_id)
    if not product:
        return False
    product.is_deleted = True
    await db.commit()
    return True
