import uuid
from typing import Any
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.account import Account, AccountType
from app.models.collection import Collection
from app.models.contra import ContraEntry
from app.models.expense import Expense
from app.schemas.account import AccountCreate, AccountUpdate


async def get_account(db: AsyncSession, account_id: uuid.UUID) -> Account | None:
    result = await db.execute(
        select(Account).where(Account.id == account_id, Account.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


async def list_accounts(
    db: AsyncSession,
    type: str | None = None,
    is_active: bool | None = None,
) -> list[Account]:
    query = select(Account).where(Account.is_deleted.is_(False))
    if type:
        query = query.where(Account.type == type)
    if is_active is not None:
        query = query.where(Account.is_active == is_active)

    query = query.order_by(Account.created_at.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_account(
    db: AsyncSession, data: AccountCreate, created_by: uuid.UUID
) -> Account:
    account = Account(
        name=data.name,
        type=data.type,
        account_no=data.account_no,
        opening_balance=Decimal(str(data.opening_balance)),
        is_active=data.is_active,
        created_by=created_by,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def update_account(
    db: AsyncSession, account_id: uuid.UUID, data: AccountUpdate
) -> Account | None:
    account = await get_account(db, account_id)
    if not account:
        return None

    if data.name is not None:
        account.name = data.name
    if data.account_no is not None:
        account.account_no = data.account_no
    if data.is_active is not None:
        account.is_active = data.is_active

    await db.commit()
    await db.refresh(account)
    return account


async def delete_account(db: AsyncSession, account_id: uuid.UUID) -> bool:
    account = await get_account(db, account_id)
    if not account:
        return False

    account.is_deleted = True
    account.is_active = False
    await db.commit()
    return True


async def compute_balance(db: AsyncSession, account_id: uuid.UUID) -> Decimal:
    account = await get_account(db, account_id)
    if not account:
        raise ValueError("Account not found")

    balance = Decimal(str(account.opening_balance))

    # Collections (Inflow)
    col_result = await db.execute(
        select(func.sum(Collection.amount)).where(
            Collection.account_id == account_id,
            Collection.is_deleted.is_(False)
        )
    )
    collections_sum = col_result.scalar() or Decimal("0.00")
    balance += collections_sum

    # Contra Inflow
    contra_in_result = await db.execute(
        select(func.sum(ContraEntry.amount)).where(
            ContraEntry.to_account_id == account_id,
            ContraEntry.is_deleted.is_(False)
        )
    )
    contra_in_sum = contra_in_result.scalar() or Decimal("0.00")
    balance += contra_in_sum

    # Expenses (Outflow)
    exp_result = await db.execute(
        select(func.sum(Expense.amount)).where(
            Expense.account_id == account_id,
            Expense.is_deleted.is_(False)
        )
    )
    expenses_sum = exp_result.scalar() or Decimal("0.00")
    balance -= expenses_sum

    # Contra Outflow
    contra_out_result = await db.execute(
        select(func.sum(ContraEntry.amount)).where(
            ContraEntry.from_account_id == account_id,
            ContraEntry.is_deleted.is_(False)
        )
    )
    contra_out_sum = contra_out_result.scalar() or Decimal("0.00")
    balance -= contra_out_sum

    return balance

async def get_accounts_with_balances(
    db: AsyncSession,
    type: str | None = None,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    accounts = await list_accounts(db, type=type, is_active=is_active)
    
    result = []
    for account in accounts:
        balance = await compute_balance(db, account.id)
        result.append({
            "id": account.id,
            "name": account.name,
            "type": account.type,
            "account_no": account.account_no,
            "opening_balance": account.opening_balance,
            "is_active": account.is_active,
            "created_at": account.created_at,
            "updated_at": account.updated_at,
            "current_balance": float(balance)
        })
    return result
