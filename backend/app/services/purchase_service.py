"""
Purchase business logic service.

CRITICAL: Receiving a purchase (DRAFT → RECEIVED) creates stock_movements
in a SINGLE atomic DB transaction (INSTRUCTION.md §5, §7).
"""
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.purchase import Purchase, PurchaseItem, PurchaseStatus
from app.models.stock_movement import MovementType, StockMovement
from app.schemas.purchase import PurchaseCreate, PurchaseUpdate


async def _compute_totals(
    db: AsyncSession, items_data: list, discount: Decimal
) -> tuple[Decimal, Decimal, Decimal, list[dict]]:
    """
    Compute subtotal, vat_amount, total for the purchase and enrich item data.
    Returns (subtotal, vat_amount, total, enriched_items).
    All arithmetic uses Decimal — never float.
    """
    subtotal = Decimal("0.00")
    enriched = []

    for item in items_data:
        product_result = await db.execute(
            select(Product).where(Product.id == item.product_id, Product.is_deleted.is_(False))
        )
        product = product_result.scalar_one_or_none()
        if not product:
            raise ValueError(f"Product {item.product_id} not found or inactive")

        total_pcs = (item.qty_carton * product.pcs_per_carton) + item.qty_pcs
        if total_pcs <= 0:
            raise ValueError(f"Product {product.name_en}: total pieces must be > 0")

        line_total = Decimal(str(total_pcs)) * item.buy_price
        subtotal += line_total

        enriched.append({
            "product_id": item.product_id,
            "product": product,
            "qty_carton": item.qty_carton,
            "qty_pcs": item.qty_pcs,
            "total_pieces": total_pcs,
            "buy_price": item.buy_price,
            "line_total": line_total,
        })

    vat_amount = Decimal("0.00")  # VAT on purchases computed separately if needed
    total = subtotal - discount + vat_amount
    return subtotal, vat_amount, total, enriched


async def get_purchase(db: AsyncSession, purchase_id: uuid.UUID) -> Purchase | None:
    result = await db.execute(
        select(Purchase)
        .options(selectinload(Purchase.items).selectinload(PurchaseItem.product))
        .options(selectinload(Purchase.supplier))
        .where(Purchase.id == purchase_id, Purchase.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


async def list_purchases(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    supplier_id: uuid.UUID | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[list[Purchase], int]:
    query = (
        select(Purchase)
        .options(selectinload(Purchase.supplier))
        .where(Purchase.is_deleted.is_(False))
    )
    if supplier_id:
        query = query.where(Purchase.supplier_id == supplier_id)
    if status:
        query = query.where(Purchase.status == status)
    if date_from:
        query = query.where(Purchase.purchase_date >= date_from)
    if date_to:
        query = query.where(Purchase.purchase_date <= date_to)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar() or 0

    query = (
        query.order_by(Purchase.purchase_date.desc(), Purchase.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def create_purchase(
    db: AsyncSession, data: PurchaseCreate, created_by: uuid.UUID
) -> Purchase:
    """Create purchase in DRAFT status. No stock movement yet."""
    discount = data.discount or Decimal("0.00")
    subtotal, vat_amount, total, enriched = await _compute_totals(db, data.items, discount)

    purchase = Purchase(
        supplier_id=data.supplier_id,
        purchase_date=data.purchase_date,
        invoice_no=data.invoice_no,
        subtotal=subtotal,
        vat_amount=vat_amount,
        discount=discount,
        total=total,
        paid=Decimal("0.00"),
        status=PurchaseStatus.DRAFT,
        notes=data.notes,
        created_by=created_by,
    )
    db.add(purchase)
    await db.flush()  # get purchase.id

    for item_data in enriched:
        item = PurchaseItem(
            purchase_id=purchase.id,
            product_id=item_data["product_id"],
            qty_carton=item_data["qty_carton"],
            qty_pcs=item_data["qty_pcs"],
            total_pieces=item_data["total_pieces"],
            buy_price=item_data["buy_price"],
            line_total=item_data["line_total"],
        )
        db.add(item)

    await db.commit()
    await db.refresh(purchase)
    return purchase


async def receive_purchase(
    db: AsyncSession, purchase_id: uuid.UUID, paid: Decimal, received_by: uuid.UUID
) -> Purchase:
    """
    Mark purchase as RECEIVED and create stock_movements atomically.
    INSTRUCTION.md §7: financial write operations in single transaction.
    """
    async with db.begin_nested():  # savepoint for atomicity
        purchase = await get_purchase(db, purchase_id)
        if not purchase:
            raise ValueError("Purchase not found")
        if purchase.status != PurchaseStatus.DRAFT:
            raise ValueError(f"Cannot receive purchase in status '{purchase.status.value}'")

        purchase.status = PurchaseStatus.RECEIVED
        purchase.paid = paid

        # Create one StockMovement per purchase item
        for item in purchase.items:
            movement = StockMovement(
                product_id=item.product_id,
                movement_type=MovementType.PURCHASE,
                qty_pieces=item.total_pieces,
                unit_price=item.buy_price,
                movement_date=purchase.purchase_date,
                reference_id=purchase.id,
                reference_type="purchase",
                notes=f"Purchase received: {purchase.invoice_no or str(purchase.id)[:8]}",
                is_approved=True,
                created_by=received_by,
            )
            db.add(movement)

    await db.commit()
    await db.refresh(purchase)
    return purchase


async def cancel_purchase(db: AsyncSession, purchase_id: uuid.UUID) -> Purchase:
    """Cancel a DRAFT purchase. Cannot cancel RECEIVED."""
    purchase = await get_purchase(db, purchase_id)
    if not purchase:
        raise ValueError("Purchase not found")
    if purchase.status == PurchaseStatus.RECEIVED:
        raise ValueError("Cannot cancel a received purchase. Create a return instead.")
    purchase.status = PurchaseStatus.CANCELLED
    await db.commit()
    return purchase
