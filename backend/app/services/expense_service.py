import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.expense import Expense, ExpenseHead
from app.schemas.expense import ExpenseCreate, ExpenseHeadCreate, ExpenseHeadUpdate


# --- Expense Head ---

async def get_expense_head(db: AsyncSession, head_id: uuid.UUID) -> ExpenseHead | None:
    result = await db.execute(select(ExpenseHead).where(ExpenseHead.id == head_id))
    return result.scalar_one_or_none()

async def list_expense_heads(
    db: AsyncSession, is_active: bool | None = None
) -> list[ExpenseHead]:
    query = select(ExpenseHead)
    if is_active is not None:
        query = query.where(ExpenseHead.is_active == is_active)
    query = query.order_by(ExpenseHead.name)
    result = await db.execute(query)
    return list(result.scalars().all())

async def create_expense_head(db: AsyncSession, data: ExpenseHeadCreate) -> ExpenseHead:
    head = ExpenseHead(
        name=data.name,
        description=data.description,
        is_active=data.is_active,
    )
    db.add(head)
    await db.commit()
    await db.refresh(head)
    return head

async def update_expense_head(
    db: AsyncSession, head_id: uuid.UUID, data: ExpenseHeadUpdate
) -> ExpenseHead | None:
    head = await get_expense_head(db, head_id)
    if not head:
        return None
    if data.name is not None:
        head.name = data.name
    if data.description is not None:
        head.description = data.description
    if data.is_active is not None:
        head.is_active = data.is_active
    await db.commit()
    await db.refresh(head)
    return head

# --- Expense ---

async def get_expense(db: AsyncSession, expense_id: uuid.UUID) -> Expense | None:
    result = await db.execute(
        select(Expense)
        .options(selectinload(Expense.head), selectinload(Expense.account))
        .where(Expense.id == expense_id, Expense.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()

async def list_expenses(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    head_id: uuid.UUID | None = None,
    account_id: uuid.UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[list[Expense], int]:
    query = select(Expense).where(Expense.is_deleted.is_(False))
    if head_id:
        query = query.where(Expense.head_id == head_id)
    if account_id:
        query = query.where(Expense.account_id == account_id)
    if date_from:
        try:
            d_from = date.fromisoformat(date_from) if isinstance(date_from, str) else date_from
            query = query.where(Expense.date >= d_from)
        except ValueError:
            pass
    if date_to:
        try:
            d_to = date.fromisoformat(date_to) if isinstance(date_to, str) else date_to
            query = query.where(Expense.date <= d_to)
        except ValueError:
            pass

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar() or 0

    query = (
        query.options(selectinload(Expense.head), selectinload(Expense.account))
        .order_by(Expense.date.desc(), Expense.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    return list(result.scalars().all()), total

async def create_expense(
    db: AsyncSession, data: ExpenseCreate, created_by: uuid.UUID
) -> Expense:
    # Check if head exists
    head = await get_expense_head(db, data.head_id)
    if not head or not head.is_active:
        raise ValueError("Invalid or inactive Expense Head")

    expense = Expense(
        head_id=data.head_id,
        amount=Decimal(str(data.amount)),
        date=data.date,
        account_id=data.account_id,
        description=data.description,
        reference=data.reference,
        created_by=created_by,
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    
    # Load relationships for return
    return await get_expense(db, expense.id)

async def delete_expense(db: AsyncSession, expense_id: uuid.UUID) -> bool:
    expense = await get_expense(db, expense_id)
    if not expense:
        return False
    expense.is_deleted = True
    await db.commit()
    return True
