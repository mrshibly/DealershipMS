import uuid
from datetime import date
from decimal import Decimal
from math import ceil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.account import Account
from app.models.supplier import Supplier
from app.models.supplier_payment import SupplierPayment
from app.schemas.supplier_payment import SupplierPaymentCreate
from app.services import account_service


async def create_supplier_payment(
    db: AsyncSession, data: SupplierPaymentCreate, created_by: uuid.UUID
) -> SupplierPayment:
    # Validate supplier exists
    supplier_res = await db.execute(select(Supplier).where(Supplier.id == data.supplier_id, Supplier.is_deleted.is_(False)))
    supplier = supplier_res.scalar_one_or_none()
    if not supplier:
        raise ValueError("Supplier not found or inactive")

    # Validate account exists
    account_res = await db.execute(select(Account).where(Account.id == data.account_id, Account.is_deleted.is_(False)))
    account = account_res.scalar_one_or_none()
    if not account:
        raise ValueError("Bank/Cash Account not found or inactive")

    # Check account balance
    balance = await account_service.compute_balance(db, data.account_id)
    if balance < data.amount:
        raise ValueError(f"Insufficient funds in account '{account.name}'. Available: Tk. {balance:,.2f}")

    payment = SupplierPayment(
        supplier_id=data.supplier_id,
        account_id=data.account_id,
        amount=data.amount,
        payment_date=data.payment_date,
        description=data.description,
        created_by=created_by,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def list_supplier_payments(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    supplier_id: uuid.UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[list[SupplierPayment], int]:
    query = select(SupplierPayment).options(
        selectinload(SupplierPayment.supplier),
        selectinload(SupplierPayment.account),
    ).where(SupplierPayment.is_deleted.is_(False))

    if supplier_id:
        query = query.where(SupplierPayment.supplier_id == supplier_id)
    if date_from:
        try:
            d_from = date.fromisoformat(date_from)
            query = query.where(SupplierPayment.payment_date >= d_from)
        except ValueError:
            pass
    if date_to:
        try:
            d_to = date.fromisoformat(date_to)
            query = query.where(SupplierPayment.payment_date <= d_to)
        except ValueError:
            pass

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar() or 0

    query = (
        query.order_by(SupplierPayment.payment_date.desc(), SupplierPayment.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def void_supplier_payment(db: AsyncSession, payment_id: uuid.UUID) -> SupplierPayment:
    result = await db.execute(select(SupplierPayment).where(SupplierPayment.id == payment_id, SupplierPayment.is_deleted.is_(False)))
    payment = result.scalar_one_or_none()
    if not payment:
        raise ValueError("Supplier payment not found")

    payment.is_deleted = True
    await db.commit()
    await db.refresh(payment)
    return payment
