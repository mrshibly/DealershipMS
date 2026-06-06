from datetime import date
from typing import Any
from decimal import Decimal
import uuid

from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.invoice import Invoice, InvoiceItem, InvoiceStatus
from app.models.collection import Collection
from app.models.expense import Expense
from app.models.purchase import Purchase, PurchaseItem, PurchaseStatus
from app.models.stock_movement import StockMovement
from app.models.product import Product

async def get_daybook(db: AsyncSession, day: date) -> dict[str, Any]:
    """
    Daybook summarizes the financial activity for a specific date:
    Collections (Inflow), Expenses (Outflow), Purchases Paid (Outflow), and Total Sales generated.
    """
    # 1. Collections (Cash IN)
    collections = await db.execute(
        select(Collection)
        .options(selectinload(Collection.invoice), selectinload(Collection.account))
        .where(Collection.date == day, Collection.is_deleted.is_(False))
    )
    col_list = collections.scalars().all()
    total_inflow = sum(c.amount for c in col_list)
    
    # 2. Expenses (Cash OUT)
    expenses = await db.execute(
        select(Expense)
        .options(selectinload(Expense.head), selectinload(Expense.account))
        .where(Expense.date == day, Expense.is_deleted.is_(False))
    )
    exp_list = expenses.scalars().all()
    
    # 3. Purchases (Cash OUT - assuming paid on same day for simplicity of daybook)
    # If partial payments to suppliers exist, we'd query a SupplierPayment table.
    # For now, we take 'paid' amount of purchases received on this date.
    purchases = await db.execute(
        select(Purchase)
        .options(selectinload(Purchase.supplier))
        .where(Purchase.purchase_date == day, Purchase.is_deleted.is_(False))
    )
    pur_list = purchases.scalars().all()
    total_outflow = sum(e.amount for e in exp_list) + sum(p.paid for p in pur_list)

    # 4. Total Sales (Booked revenue, not necessarily cash)
    invoices = await db.execute(
        select(Invoice)
        .where(
            Invoice.date == day,
            Invoice.is_deleted.is_(False),
            Invoice.status != InvoiceStatus.VOID
        )
    )
    inv_list = invoices.scalars().all()
    total_sales = sum(i.grand_total for i in inv_list)

    # Prepare data for Excel/JSON
    transactions = []
    for c in col_list:
        transactions.append({
            "type": "Collection",
            "reference": c.invoice.invoice_no if c.invoice else str(c.id)[:8],
            "account": c.account.name if c.account else "Unknown",
            "inflow": float(c.amount),
            "outflow": 0.0,
            "narration": f"Collection from {c.payment_method}"
        })
    for e in exp_list:
        transactions.append({
            "type": "Expense",
            "reference": e.reference or str(e.id)[:8],
            "account": e.account.name if e.account else "Unknown",
            "inflow": 0.0,
            "outflow": float(e.amount),
            "narration": f"Expense: {e.head.name if e.head else ''} - {e.description or ''}"
        })
    for p in pur_list:
        if p.paid > 0:
            transactions.append({
                "type": "Purchase Payment",
                "reference": p.invoice_no or str(p.id)[:8],
                "account": "Unknown", # Depending on how purchase payment was recorded
                "inflow": 0.0,
                "outflow": float(p.paid),
                "narration": f"Paid to supplier: {p.supplier.name if p.supplier else ''}"
            })

    return {
        "summary": {
            "date": str(day),
            "total_inflow": float(total_inflow),
            "total_outflow": float(total_outflow),
            "net_cash_flow": float(total_inflow - Decimal(str(total_outflow))),
            "total_sales_booked": float(total_sales)
        },
        "transactions": transactions
    }

async def get_sales_report(
    db: AsyncSession, date_from: date, date_to: date, dsr_id: uuid.UUID = None, dealer_id: uuid.UUID = None
) -> list[dict[str, Any]]:
    query = select(Invoice).options(
        selectinload(Invoice.dsr), selectinload(Invoice.dealer), selectinload(Invoice.shop)
    ).where(
        Invoice.date >= date_from,
        Invoice.date <= date_to,
        Invoice.is_deleted.is_(False),
        Invoice.status != InvoiceStatus.VOID
    )
    if dsr_id:
        query = query.where(Invoice.dsr_id == dsr_id)
    if dealer_id:
        query = query.where(Invoice.dealer_id == dealer_id)

    query = query.order_by(Invoice.date.asc())
    invoices = (await db.execute(query)).scalars().all()

    return [
        {
            "date": str(inv.date),
            "invoice_no": inv.invoice_no,
            "dsr_name": inv.dsr.name if inv.dsr else "-",
            "dealer_name": inv.dealer.name if inv.dealer else "-",
            "shop_name": inv.shop.name if inv.shop else "-",
            "subtotal": float(inv.subtotal),
            "discount": float(inv.discount),
            "vat_amount": float(inv.vat_amount),
            "grand_total": float(inv.grand_total),
            "paid_amount": float(inv.paid_amount),
            "due": float(inv.grand_total - inv.paid_amount),
            "status": inv.status.value
        }
        for inv in invoices
    ]

async def get_product_sales_report(
    db: AsyncSession, date_from: date, date_to: date
) -> list[dict[str, Any]]:
    # Sum product sales across all valid invoices in the date range
    query = (
        select(
            Product.sku,
            Product.name_en,
            func.sum(InvoiceItem.total_pieces).label("total_sold"),
            func.sum(InvoiceItem.line_total).label("total_revenue")
        )
        .join(InvoiceItem, InvoiceItem.product_id == Product.id)
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .where(
            Invoice.date >= date_from,
            Invoice.date <= date_to,
            Invoice.is_deleted.is_(False),
            Invoice.status != InvoiceStatus.VOID
        )
        .group_by(Product.id)
        .order_by(func.sum(InvoiceItem.line_total).desc())
    )
    
    result = await db.execute(query)
    
    return [
        {
            "sku": row.sku,
            "product_name": row.name_en,
            "quantity_sold": int(row.total_sold or 0),
            "total_revenue": float(row.total_revenue or 0)
        }
        for row in result.all()
    ]

async def get_profit_report(
    db: AsyncSession, date_from: date, date_to: date
) -> list[dict[str, Any]]:
    """
    Calculates profit per product based on (unit_price - buy_price) * total_pieces.
    We estimate the buy_price using the product's base price for simplicity.
    A more accurate FIFO profit calculation is complex, so we use standard cost estimation.
    """
    query = (
        select(
            Product.sku,
            Product.name_en,
            Product.price.label("base_buy_price"),
            func.sum(InvoiceItem.total_pieces).label("total_sold"),
            func.sum(InvoiceItem.line_total).label("total_revenue")
        )
        .join(InvoiceItem, InvoiceItem.product_id == Product.id)
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .where(
            Invoice.date >= date_from,
            Invoice.date <= date_to,
            Invoice.is_deleted.is_(False),
            Invoice.status != InvoiceStatus.VOID,
            InvoiceItem.is_free.is_(False)  # Free items don't generate revenue
        )
        .group_by(Product.id)
    )
    
    result = await db.execute(query)
    
    data = []
    for row in result.all():
        # This is a simplified profit calculation. In a real scenario, we might
        # track the exact buy_price of the batch that was sold (FIFO/LIFO).
        # We will assume a 20% margin for the sake of the report if buy_price isn't tracked properly.
        estimated_buy_price = float(row.base_buy_price) * 0.8
        revenue = float(row.total_revenue or 0)
        qty = int(row.total_sold or 0)
        
        cogs = estimated_buy_price * qty
        gross_profit = revenue - cogs
        
        data.append({
            "sku": row.sku,
            "product_name": row.name_en,
            "quantity_sold": qty,
            "total_revenue": revenue,
            "estimated_cogs": cogs,
            "gross_profit": gross_profit,
            "margin_pct": round((gross_profit / revenue) * 100, 2) if revenue > 0 else 0
        })
        
    # Sort by profit
    data.sort(key=lambda x: x["gross_profit"], reverse=True)
    return data

async def get_vat_report(
    db: AsyncSession, date_from: date, date_to: date
) -> list[dict[str, Any]]:
    query = select(Invoice).options(selectinload(Invoice.dealer)).where(
        Invoice.date >= date_from,
        Invoice.date <= date_to,
        Invoice.is_deleted.is_(False),
        Invoice.status != InvoiceStatus.VOID,
        Invoice.vat_amount > 0
    ).order_by(Invoice.date.asc())
    
    invoices = (await db.execute(query)).scalars().all()
    
    return [
        {
            "date": str(inv.date),
            "invoice_no": inv.invoice_no,
            "dealer_name": inv.dealer.name if inv.dealer else "-",
            "subtotal": float(inv.subtotal),
            "vat_amount": float(inv.vat_amount),
            "total_with_vat": float(inv.subtotal - inv.discount + inv.vat_amount)
        }
        for inv in invoices
    ]

async def get_stock_movement_report(
    db: AsyncSession, product_id: uuid.UUID
) -> list[dict[str, Any]]:
    query = select(StockMovement).where(
        StockMovement.product_id == product_id,
        StockMovement.is_approved.is_(True),
        StockMovement.is_deleted.is_(False)
    ).order_by(StockMovement.movement_date.asc(), StockMovement.created_at.asc())
    
    movements = (await db.execute(query)).scalars().all()
    
    data = []
    running_balance = 0
    for m in movements:
        # Determine sign based on MovementType
        if m.movement_type.value in ("OPENING", "PURCHASE", "SALES_RETURN", "ADJUSTMENT_IN", "ROUTE_RETURN"):
            qty = m.qty_pieces
        else:
            qty = -m.qty_pieces
            
        running_balance += qty
        
        data.append({
            "date": str(m.movement_date),
            "type": m.movement_type.value,
            "reference_id": str(m.reference_id) if m.reference_id else "-",
            "qty_change": qty,
            "running_balance": running_balance,
            "notes": m.notes or "-"
        })
        
    return data
