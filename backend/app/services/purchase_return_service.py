import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.purchase import Purchase
from app.models.purchase_return import PurchaseReturn, PurchaseReturnItem, PurchaseReturnStatus
from app.models.stock_movement import MovementType, StockMovement
from app.models.supplier import Supplier
from app.schemas.purchase_return import PurchaseReturnCreate
from app.services import inventory_service


async def generate_return_number(db: AsyncSession) -> str:
    year = date.today().year
    prefix = f"PR-{year}-"
    result = await db.execute(
        select(PurchaseReturn.return_no)
        .where(PurchaseReturn.return_no.like(f"{prefix}%"))
    )
    nos = result.scalars().all()
    seqs = []
    for no in nos:
        try:
            parts = no.split("-")
            if len(parts) == 3:
                seqs.append(int(parts[2]))
        except ValueError:
            pass
    max_seq = max(seqs) if seqs else 0
    new_seq = max_seq + 1
    
    while True:
        candidate = f"{prefix}{new_seq:05d}"
        chk = await db.execute(select(PurchaseReturn.id).where(PurchaseReturn.return_no == candidate))
        if not chk.scalar_one_or_none():
            return candidate
        new_seq += 1


async def create_purchase_return(
    db: AsyncSession, data: PurchaseReturnCreate, created_by: uuid.UUID
) -> PurchaseReturn:
    # Validate supplier exists
    supplier_res = await db.execute(select(Supplier).where(Supplier.id == data.supplier_id, Supplier.is_deleted.is_(False)))
    if not supplier_res.scalar_one_or_none():
        raise ValueError("Supplier not found or inactive")

    # Validate purchase exists if reference_id provided
    if data.purchase_id:
        purchase_res = await db.execute(select(Purchase).where(Purchase.id == data.purchase_id, Purchase.is_deleted.is_(False)))
        if not purchase_res.scalar_one_or_none():
            raise ValueError("Purchase invoice not found")

    return_no = await generate_return_number(db)
    
    purchase_return = PurchaseReturn(
        supplier_id=data.supplier_id,
        purchase_id=data.purchase_id,
        return_no=return_no,
        return_date=data.return_date,
        discount=data.discount,
        notes=data.notes,
        status=PurchaseReturnStatus.DRAFT,
        created_by=created_by,
    )
    db.add(purchase_return)
    await db.flush()  # get purchase_return.id

    subtotal = Decimal("0.00")
    for item_data in data.items:
        product_res = await db.execute(select(Product).where(Product.id == item_data.product_id, Product.is_deleted.is_(False)))
        product = product_res.scalar_one_or_none()
        if not product:
            raise ValueError(f"Product {item_data.product_id} not found")

        total_pieces = (item_data.qty_carton * product.pcs_per_carton) + item_data.qty_pcs
        if total_pieces <= 0:
            raise ValueError(f"Return quantity for product {product.name_en} must be greater than 0")

        # Verify stock levels
        level = await inventory_service.get_stock_level(db, product)
        if total_pieces > level["qty_pieces"]:
            raise ValueError(
                f"Insufficient stock for return. Product: {product.name_en}. "
                f"Available: {level['qty_pieces']} pcs, requested: {total_pieces} pcs"
            )

        line_total = Decimal(str(total_pieces)) * item_data.return_price
        subtotal += line_total

        return_item = PurchaseReturnItem(
            purchase_return_id=purchase_return.id,
            product_id=item_data.product_id,
            qty_carton=item_data.qty_carton,
            qty_pcs=item_data.qty_pcs,
            total_pieces=total_pieces,
            return_price=item_data.return_price,
            line_total=line_total,
        )
        db.add(return_item)

    purchase_return.subtotal = subtotal
    purchase_return.total_receivable = subtotal - data.discount

    await db.commit()
    await db.refresh(purchase_return)
    return purchase_return


async def confirm_purchase_return(
    db: AsyncSession, return_id: uuid.UUID, confirmed_by: uuid.UUID
) -> PurchaseReturn:
    async with db.begin_nested():
        result = await db.execute(
            select(PurchaseReturn)
            .options(
                selectinload(PurchaseReturn.items).selectinload(PurchaseReturnItem.product),
                selectinload(PurchaseReturn.supplier)
            )
            .where(PurchaseReturn.id == return_id, PurchaseReturn.is_deleted.is_(False))
        )
        purchase_return = result.scalar_one_or_none()
        if not purchase_return:
            raise ValueError("Purchase return not found")
        if purchase_return.status != PurchaseReturnStatus.DRAFT:
            raise ValueError(f"Cannot confirm return in status '{purchase_return.status.value}'")

        purchase_return.status = PurchaseReturnStatus.CONFIRMED

        # Create stock movements (reducing inventory)
        for item in purchase_return.items:
            # Re-check stock levels at confirmation time
            level = await inventory_service.get_stock_level(db, item.product)
            if item.total_pieces > level["qty_pieces"]:
                raise ValueError(
                    f"Insufficient stock to complete return. Product: {item.product.name_en}. "
                    f"Available: {level['qty_pieces']} pcs, requested: {item.total_pieces} pcs"
                )

            movement = StockMovement(
                product_id=item.product_id,
                movement_type=MovementType.PURCHASE_RETURN,
                qty_pieces=item.total_pieces,
                unit_price=item.return_price,
                movement_date=purchase_return.return_date,
                reference_id=purchase_return.id,
                reference_type="purchase_return",
                notes=f"Purchase return: {purchase_return.return_no}",
                is_approved=True,
                created_by=confirmed_by,
            )
            db.add(movement)

    await db.commit()
    await db.refresh(purchase_return)
    return purchase_return


async def void_purchase_return(db: AsyncSession, return_id: uuid.UUID) -> PurchaseReturn:
    result = await db.execute(select(PurchaseReturn).where(PurchaseReturn.id == return_id, PurchaseReturn.is_deleted.is_(False)))
    purchase_return = result.scalar_one_or_none()
    if not purchase_return:
        raise ValueError("Purchase return not found")
    if purchase_return.status == PurchaseReturnStatus.CONFIRMED:
        raise ValueError("Cannot void a confirmed purchase return")

    purchase_return.is_deleted = True
    await db.commit()
    return purchase_return


async def get_purchase_return_detail(db: AsyncSession, return_id: uuid.UUID) -> PurchaseReturn | None:
    result = await db.execute(
        select(PurchaseReturn)
        .options(
            selectinload(PurchaseReturn.items).selectinload(PurchaseReturnItem.product),
            selectinload(PurchaseReturn.supplier),
            selectinload(PurchaseReturn.purchase)
        )
        .where(PurchaseReturn.id == return_id, PurchaseReturn.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


async def list_purchase_returns(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    supplier_id: uuid.UUID | None = None,
    status: str | None = None,
) -> tuple[list[PurchaseReturn], int]:
    query = (
        select(PurchaseReturn)
        .options(selectinload(PurchaseReturn.supplier), selectinload(PurchaseReturn.purchase))
        .where(PurchaseReturn.is_deleted.is_(False))
    )
    if supplier_id:
        query = query.where(PurchaseReturn.supplier_id == supplier_id)
    if status:
        query = query.where(PurchaseReturn.status == status)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar() or 0

    query = (
        query.order_by(PurchaseReturn.return_date.desc(), PurchaseReturn.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    return list(result.scalars().all()), total
