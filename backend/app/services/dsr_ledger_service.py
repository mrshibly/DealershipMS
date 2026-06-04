"""
DSR Ledger service.

Aggregates invoices, collections, and commission for a specific DSR.
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection import Collection
from app.models.dsr import DSR
from app.models.invoice import Invoice, InvoiceStatus


async def get_dsr_ledger(
    db: AsyncSession,
    dsr_id: uuid.UUID,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict[str, Any]:
    """
    Returns DSR ledger summary and invoice-level breakdown.
    """
    # Verify DSR exists
    dsr_result = await db.execute(
        select(DSR).where(DSR.id == dsr_id, DSR.is_deleted.is_(False))
    )
    dsr = dsr_result.scalar_one_or_none()
    if not dsr:
        return None

    # Build invoice query for this DSR
    inv_q = select(Invoice).where(
        Invoice.dsr_id == dsr_id,
        Invoice.is_deleted.is_(False),
        Invoice.status != InvoiceStatus.VOID,
    )
    if date_from:
        inv_q = inv_q.where(Invoice.date >= date_from)
    if date_to:
        inv_q = inv_q.where(Invoice.date <= date_to)

    inv_result = await db.execute(inv_q.order_by(Invoice.date.desc()))
    invoices = inv_result.scalars().all()

    # Aggregate totals
    total_sales = sum(i.grand_total for i in invoices)
    total_collected = sum(i.paid_amount for i in invoices)
    total_outstanding = total_sales - total_collected

    # Commission = total_sales × (commission_rate / 100)
    commission_rate = Decimal(str(dsr.commission_rate))
    commission_earned = total_sales * (commission_rate / Decimal("100"))

    # Collections made by this DSR (across all invoices in the period)
    col_q = select(
        func.sum(Collection.amount)
    ).where(
        Collection.dsr_id == dsr_id,
        Collection.is_deleted.is_(False),
    )
    if date_from:
        col_q = col_q.where(Collection.collected_at >= date_from)
    if date_to:
        col_q = col_q.where(Collection.collected_at <= date_to)

    col_sum = await db.scalar(col_q) or Decimal("0.00")

    # Invoice rows for ledger
    invoice_rows = []
    running_balance = Decimal("0.00")
    for inv in sorted(invoices, key=lambda x: x.date):
        running_balance += (inv.grand_total - inv.paid_amount)
        invoice_rows.append({
            "id": str(inv.id),
            "invoice_no": inv.invoice_no,
            "date": str(inv.date),
            "grand_total": inv.grand_total,
            "paid_amount": inv.paid_amount,
            "outstanding": inv.grand_total - inv.paid_amount,
            "status": inv.status.value,
            "running_balance": running_balance,
        })

    return {
        "dsr": {
            "id": str(dsr.id),
            "name": dsr.name,
            "phone": dsr.phone,
            "commission_rate": str(dsr.commission_rate),
        },
        "summary": {
            "total_invoices": len(invoices),
            "total_sales": total_sales,
            "total_collected": total_collected,
            "total_outstanding": total_outstanding,
            "total_collections_received": col_sum,
            "commission_rate": str(commission_rate),
            "commission_earned": commission_earned,
        },
        "invoices": invoice_rows,
    }
