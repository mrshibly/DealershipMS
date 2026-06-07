"""
Invoice service.

Handles creation, confirmation, voiding, and payments for invoices.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.collection import Collection, PaymentMethod
from app.models.invoice import Invoice, InvoiceItem, InvoiceStatus
from app.models.product import Product
from app.models.stock_movement import StockMovement, MovementType
from app.models.dsr import DSR
from app.schemas.invoice import InvoiceCreate
from app.schemas.collection import CollectPaymentRequest
from app.services.sms_service import send_sms_notification


async def generate_invoice_number(db: AsyncSession) -> str:
    """Generate sequential invoice number: INV-YYYY-XXXXX"""
    year = datetime.utcnow().year
    prefix = f"INV-{year}-"
    
    # Select all invoice numbers for this year to find the true numeric maximum
    stmt = select(Invoice.invoice_no).where(
        Invoice.invoice_no.like(f"{prefix}%")
    )
    result = await db.execute(stmt)
    invoice_nos = result.scalars().all()
    
    max_seq = 0
    for num in invoice_nos:
        try:
            parts = num.split("-")
            if len(parts) >= 3:
                seq = int(parts[2])
                if seq > max_seq:
                    max_seq = seq
        except (IndexError, ValueError):
            continue
            
    new_seq = max_seq + 1
    
    # Defensively check candidate invoice numbers to guarantee uniqueness
    while True:
        candidate = f"{prefix}{new_seq:05d}"
        chk = await db.execute(select(Invoice.id).where(Invoice.invoice_no == candidate))
        if not chk.scalar_one_or_none():
            return candidate
        new_seq += 1


async def get_invoice_detail(db: AsyncSession, invoice_id: uuid.UUID) -> Invoice:
    stmt = (
        select(Invoice)
        .options(
            selectinload(Invoice.items).selectinload(InvoiceItem.product).selectinload(Product.category),
            selectinload(Invoice.collections),
            selectinload(Invoice.dealer),
            selectinload(Invoice.dsr),
            selectinload(Invoice.shop),
        )
        .where(Invoice.id == invoice_id, Invoice.is_deleted == False)
    )
    result = await db.execute(stmt)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    return invoice


async def create_invoice(db: AsyncSession, data: InvoiceCreate, user_id: uuid.UUID) -> Invoice:
    """
    Create a new invoice. Saved as DRAFT initially.
    """
    invoice_no = await generate_invoice_number(db)
    
    # Collect product IDs to fetch them all at once
    product_ids = [item.product_id for item in data.items]
    stmt = select(Product).where(Product.id.in_(product_ids), Product.is_active == True)
    result = await db.execute(stmt)
    products = {p.id: p for p in result.scalars().all()}
    
    # Check if any products are missing or inactive
    missing = set(product_ids) - set(products.keys())
    if missing:
        raise HTTPException(status_code=422, detail=f"Products not found or inactive: {missing}")
    
    subtotal = Decimal("0.00")
    vat_total = Decimal("0.00")
    
    invoice_items = []
    for item_data in data.items:
        product = products[item_data.product_id]
        
        # Calculate quantities
        total_pieces = (item_data.qty_carton * product.pcs_per_carton) + item_data.qty_pcs
        if total_pieces <= 0:
            raise HTTPException(status_code=422, detail=f"Quantity must be > 0 for product {product.name_en}")
            
        unit_price = Decimal(str(product.sell_price))
        line_subtotal = unit_price * Decimal(str(total_pieces))
        
        if item_data.is_free_item:
            unit_price = Decimal("0.00")
            line_subtotal = Decimal("0.00")
            vat_amount = Decimal("0.00")
            vat_rate = Decimal("0.00")
        else:
            vat_rate = product.vat_rate if product.vat_applicable else Decimal("0.00")
            vat_amount = line_subtotal * (vat_rate / Decimal("100"))
            
        line_total = line_subtotal + vat_amount
        
        subtotal += line_subtotal
        vat_total += vat_amount
        
        invoice_items.append(
            InvoiceItem(
                product_id=product.id,
                qty_carton=item_data.qty_carton,
                qty_pcs=item_data.qty_pcs,
                total_pieces=total_pieces,
                unit_price=unit_price,
                vat_rate=vat_rate,
                vat_amount=vat_amount,
                discount=Decimal("0.00"),  # Line-level discount not in schema yet
                line_total=line_total,
                is_free_item=item_data.is_free_item,
            )
        )
        
    grand_total = subtotal - data.discount + vat_total
    
    invoice = Invoice(
        invoice_no=invoice_no,
        dealer_id=data.dealer_id,
        dsr_id=data.dsr_id,
        shop_id=data.shop_id,
        date=data.date,
        subtotal=subtotal,
        vat_amount=vat_total,
        discount=data.discount,
        grand_total=grand_total,
        paid_amount=Decimal("0.00"),
        status=InvoiceStatus.DRAFT,
        notes=data.notes,
        created_by=user_id,
        items=invoice_items,
    )
    
    db.add(invoice)
    await db.flush() # flush to get invoice.id
    
    # Process payment if included during creation
    if data.payment_method and data.payment_amount and data.payment_amount > 0:
        if data.payment_amount > grand_total:
             raise HTTPException(status_code=422, detail="Payment amount cannot exceed grand total")
             
        collection = Collection(
            invoice_id=invoice.id,
            dealer_id=invoice.dealer_id,
            dsr_id=invoice.dsr_id,
            amount=data.payment_amount,
            payment_method=PaymentMethod(data.payment_method),
            reference_no=data.payment_reference,
            created_by=user_id,
        )
        db.add(collection)
        invoice.paid_amount = data.payment_amount
        
        # Note: Status remains DRAFT until explicitly confirmed, 
        # or we could auto-confirm here. 
        # For safety, let's keep it DRAFT or require caller to confirm.
        
    await db.commit()
    await db.refresh(invoice)
    
    return await get_invoice_detail(db, invoice.id)


async def confirm_invoice(db: AsyncSession, invoice_id: uuid.UUID, user_id: uuid.UUID) -> Invoice:
    """
    Confirms the invoice:
    1. Checks stock
    2. Deducts stock (creates StockMovement)
    3. Updates status based on paid amount
    """
    invoice = await get_invoice_detail(db, invoice_id)
    
    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(status_code=400, detail=f"Cannot confirm invoice in {invoice.status} status")
        
    # Check stock
    from app.services.inventory_service import get_stock_level
    
    shortages = []
    for item in invoice.items:
        stock_data = await get_stock_level(db, item.product)
        current_stock = stock_data["qty_pieces"]
        if current_stock < item.total_pieces:
            shortages.append(f"{item.product.name_en} (Need: {item.total_pieces}, Have: {current_stock})")
            
    if shortages:
        raise HTTPException(status_code=422, detail=f"Insufficient stock: {', '.join(shortages)}")
        
    # Deduct stock
    for item in invoice.items:
        movement = StockMovement(
            product_id=item.product_id,
            movement_type=MovementType.SALE,
            qty_pieces=item.total_pieces,
            reference_id=invoice.id,
            reference_type="INVOICE",
            movement_date=invoice.date,
            unit_price=item.unit_price,
            is_approved=True,
            notes=f"Invoice {invoice.invoice_no}",
            created_by=user_id,
        )
        db.add(movement)
        
    # Update status
    if invoice.paid_amount >= invoice.grand_total:
        invoice.status = InvoiceStatus.PAID
    elif invoice.paid_amount > 0:
        invoice.status = InvoiceStatus.PARTIAL
    else:
        invoice.status = InvoiceStatus.CONFIRMED
        
    await db.commit()
    return await get_invoice_detail(db, invoice_id)


async def collect_payment(db: AsyncSession, invoice_id: uuid.UUID, data: CollectPaymentRequest, user_id: uuid.UUID) -> Invoice:
    invoice = await get_invoice_detail(db, invoice_id)
    
    if invoice.status in (InvoiceStatus.VOID, InvoiceStatus.DRAFT):
        raise HTTPException(status_code=400, detail=f"Cannot collect payment for {invoice.status} invoice")
        
    outstanding = invoice.grand_total - invoice.paid_amount
    
    if outstanding <= 0:
        raise HTTPException(status_code=400, detail="Invoice is already fully paid")
        
    if data.amount > outstanding:
        raise HTTPException(status_code=422, detail=f"Payment amount ({data.amount}) exceeds outstanding balance ({outstanding})")
        
    collection = Collection(
        invoice_id=invoice.id,
        dealer_id=invoice.dealer_id,
        dsr_id=invoice.dsr_id,
        amount=data.amount,
        payment_method=data.payment_method,
        reference_no=data.reference_no,
        notes=data.notes,
        account_id=data.account_id,
        created_by=user_id,
    )
    db.add(collection)
    
    invoice.paid_amount += data.amount
    
    if invoice.paid_amount >= invoice.grand_total:
        invoice.status = InvoiceStatus.PAID
    else:
        invoice.status = InvoiceStatus.PARTIAL
        
    await db.commit()
    await db.refresh(invoice)
    
    # Send SMS Receipt via Celery
    inv_result = await db.execute(select(Invoice).options(selectinload(Invoice.dealer)).where(Invoice.id == invoice_id))
    inv = inv_result.scalar_one_or_none()
    if inv and inv.dealer and getattr(inv.dealer, 'phone', None):
        message = f"Dear {inv.dealer.name}, we have received {float(data.amount)} BDT against Invoice {inv.invoice_no}. Thank you."
        await send_sms_notification(db, inv.dealer.phone, message)

    return await get_invoice_detail(db, invoice_id)


async def void_invoice(db: AsyncSession, invoice_id: uuid.UUID, user_id: uuid.UUID) -> Invoice:
    invoice = await get_invoice_detail(db, invoice_id)
    
    if invoice.status == InvoiceStatus.VOID:
        raise HTTPException(status_code=400, detail="Invoice is already voided")
        
    if invoice.status in (InvoiceStatus.PARTIAL, InvoiceStatus.PAID):
        raise HTTPException(status_code=400, detail="Cannot void invoice with collected payments. Reverse payments first.")
        
    invoice.status = InvoiceStatus.VOID
    invoice.is_deleted = True
    
    # Reverse stock if it was confirmed
    if invoice.status != InvoiceStatus.DRAFT:
        for item in invoice.items:
            movement = StockMovement(
                product_id=item.product_id,
                movement_type=MovementType.ADJUSTMENT_IN,
                qty_pieces=item.total_pieces,
                reference_id=str(invoice.id),
                reference_type="INVOICE_VOID",
                movement_date=datetime.utcnow().date(),
                notes=f"Voided Invoice {invoice.invoice_no}",
                created_by=user_id,
            )
            db.add(movement)
            
    await db.commit()
    return invoice


async def list_invoices(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    dealer_id: uuid.UUID | None = None,
    dsr_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    status: InvoiceStatus | None = None,
) -> dict[str, Any]:
    
    query = select(Invoice).where(Invoice.is_deleted == False)
    
    if dealer_id:
        query = query.where(Invoice.dealer_id == dealer_id)
    if dsr_id:
        query = query.where(Invoice.dsr_id == dsr_id)
    if date_from:
        query = query.where(Invoice.date >= date_from)
    if date_to:
        query = query.where(Invoice.date <= date_to)
    if status:
        query = query.where(Invoice.status == status)
        
    # Count total
    count_stmt = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_stmt) or 0
    
    # Paginate
    query = (
        query.options(
            selectinload(Invoice.dealer),
            selectinload(Invoice.dsr).selectinload(DSR.route)
        )
        .order_by(desc(Invoice.date), desc(Invoice.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    pages = (total + per_page - 1) // per_page
    
    return {
        "data": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }


async def update_invoice(db: AsyncSession, invoice_id: uuid.UUID, data: InvoiceCreate, user_id: uuid.UUID) -> Invoice:
    invoice = await get_invoice_detail(db, invoice_id)
    
    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT invoices can be updated/adjusted")
        
    # Collect product IDs to fetch them all at once
    product_ids = [item.product_id for item in data.items]
    stmt = select(Product).where(Product.id.in_(product_ids), Product.is_active == True)
    result = await db.execute(stmt)
    products = {p.id: p for p in result.scalars().all()}
    
    # Check if any products are missing or inactive
    missing = set(product_ids) - set(products.keys())
    if missing:
        raise HTTPException(status_code=422, detail=f"Products not found or inactive: {missing}")
        
    # Clear old items
    invoice.items.clear()
    
    subtotal = Decimal("0.00")
    vat_total = Decimal("0.00")
    
    for item_data in data.items:
        product = products[item_data.product_id]
        
        # Calculate quantities
        total_pieces = (item_data.qty_carton * product.pcs_per_carton) + item_data.qty_pcs
        if total_pieces <= 0:
            raise HTTPException(status_code=422, detail=f"Quantity must be > 0 for product {product.name_en}")
            
        unit_price = Decimal(str(product.sell_price))
        line_subtotal = unit_price * Decimal(str(total_pieces))
        
        if item_data.is_free_item:
            unit_price = Decimal("0.00")
            line_subtotal = Decimal("0.00")
            vat_amount = Decimal("0.00")
            vat_rate = Decimal("0.00")
        else:
            vat_rate = product.vat_rate if product.vat_applicable else Decimal("0.00")
            vat_amount = line_subtotal * (vat_rate / Decimal("100"))
            
        line_total = line_subtotal + vat_amount
        
        subtotal += line_subtotal
        vat_total += vat_amount
        
        invoice.items.append(
            InvoiceItem(
                product_id=product.id,
                qty_carton=item_data.qty_carton,
                qty_pcs=item_data.qty_pcs,
                total_pieces=total_pieces,
                unit_price=unit_price,
                vat_rate=vat_rate,
                vat_amount=vat_amount,
                discount=Decimal("0.00"),
                line_total=line_total,
                is_free_item=item_data.is_free_item,
            )
        )
        
    grand_total = subtotal - data.discount + vat_total
    
    invoice.dealer_id = data.dealer_id
    invoice.dsr_id = data.dsr_id
    invoice.shop_id = data.shop_id
    invoice.date = data.date
    invoice.subtotal = subtotal
    invoice.vat_amount = vat_total
    invoice.discount = data.discount
    invoice.grand_total = grand_total
    invoice.notes = data.notes
    
    await db.commit()
    await db.refresh(invoice)
    return await get_invoice_detail(db, invoice.id)
