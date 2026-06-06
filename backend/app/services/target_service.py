import uuid
from typing import List, Optional
from datetime import date
from decimal import Decimal

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.target import Target
from app.models.invoice import Invoice, InvoiceStatus
from app.schemas.target import TargetCreate, TargetUpdate

async def get_target(db: AsyncSession, target_id: uuid.UUID) -> Optional[Target]:
    result = await db.execute(
        select(Target).options(selectinload(Target.dsr)).where(Target.id == target_id)
    )
    return result.scalar_one_or_none()

async def list_targets(db: AsyncSession, month: Optional[date] = None) -> List[Target]:
    query = select(Target).options(selectinload(Target.dsr))
    if month:
        # Match year and month
        query = query.where(
            func.extract('year', Target.target_month) == month.year,
            func.extract('month', Target.target_month) == month.month
        )
    result = await db.execute(query.order_by(Target.created_at.desc()))
    return list(result.scalars().all())

async def create_target(db: AsyncSession, data: TargetCreate) -> Target:
    target = Target(
        dsr_id=data.dsr_id,
        target_month=data.target_month.replace(day=1), # Normalize to 1st of month
        target_amount=data.target_amount
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)
    return await get_target(db, target.id)

async def update_target(db: AsyncSession, target_id: uuid.UUID, data: TargetUpdate) -> Optional[Target]:
    target = await get_target(db, target_id)
    if not target:
        return None
    if data.target_amount is not None:
        target.target_amount = data.target_amount
    await db.commit()
    await db.refresh(target)
    return target

async def calculate_achieved_amount(db: AsyncSession, dsr_id: uuid.UUID, month: date) -> float:
    """
    Calculates the actual sales (grand_total) for a specific DSR in a specific month.
    """
    result = await db.execute(
        select(func.sum(Invoice.grand_total)).where(
            Invoice.dsr_id == dsr_id,
            func.extract('year', Invoice.date) == month.year,
            func.extract('month', Invoice.date) == month.month,
            Invoice.is_deleted.is_(False),
            Invoice.status != InvoiceStatus.VOID
        )
    )
    return float(result.scalar() or Decimal("0.00"))
