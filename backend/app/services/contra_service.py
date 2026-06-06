import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contra import ContraEntry
from app.schemas.contra import ContraEntryCreate
from app.services.account_service import compute_balance, get_account

async def get_contra_entry(db: AsyncSession, contra_id: uuid.UUID) -> ContraEntry | None:
    result = await db.execute(
        select(ContraEntry)
        .options(selectinload(ContraEntry.from_account), selectinload(ContraEntry.to_account))
        .where(ContraEntry.id == contra_id, ContraEntry.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()

async def list_contra_entries(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    from_account_id: uuid.UUID | None = None,
    to_account_id: uuid.UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[list[ContraEntry], int]:
    query = select(ContraEntry).where(ContraEntry.is_deleted.is_(False))
    if from_account_id:
        query = query.where(ContraEntry.from_account_id == from_account_id)
    if to_account_id:
        query = query.where(ContraEntry.to_account_id == to_account_id)
    if date_from:
        query = query.where(ContraEntry.date >= date_from)
    if date_to:
        query = query.where(ContraEntry.date <= date_to)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar() or 0

    query = (
        query.options(selectinload(ContraEntry.from_account), selectinload(ContraEntry.to_account))
        .order_by(ContraEntry.date.desc(), ContraEntry.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    return list(result.scalars().all()), total

async def create_contra_entry(
    db: AsyncSession, data: ContraEntryCreate, created_by: uuid.UUID
) -> ContraEntry:
    if data.from_account_id == data.to_account_id:
        raise ValueError("Source and destination accounts must be different")

    async with db.begin_nested():
        from_acc = await get_account(db, data.from_account_id)
        to_acc = await get_account(db, data.to_account_id)
        
        if not from_acc or not from_acc.is_active:
            raise ValueError("Invalid source account")
        if not to_acc or not to_acc.is_active:
            raise ValueError("Invalid destination account")
            
        amount = Decimal(str(data.amount))
        
        # Check source balance
        from_balance = await compute_balance(db, data.from_account_id)
        if from_balance < amount:
            # We allow it, but we could raise an error if strict balance is required.
            pass

        entry = ContraEntry(
            from_account_id=data.from_account_id,
            to_account_id=data.to_account_id,
            amount=amount,
            date=data.date,
            narration=data.narration,
            reference=data.reference,
            created_by=created_by,
        )
        db.add(entry)
        
    await db.commit()
    await db.refresh(entry)
    
    return await get_contra_entry(db, entry.id)

async def delete_contra_entry(db: AsyncSession, contra_id: uuid.UUID) -> bool:
    entry = await get_contra_entry(db, contra_id)
    if not entry:
        return False
    entry.is_deleted = True
    await db.commit()
    return True
