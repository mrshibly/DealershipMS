"""
Supplier business logic service.
"""
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate


async def list_suppliers(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    search: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[Supplier], int]:
    query = select(Supplier).where(Supplier.is_deleted.is_(False))
    if search:
        pattern = f"%{search}%"
        from sqlalchemy import or_
        query = query.where(
            or_(Supplier.name.ilike(pattern), Supplier.phone.ilike(pattern))
        )
    if is_active is not None:
        query = query.where(Supplier.is_active.is_(is_active))

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar() or 0

    query = query.order_by(Supplier.name).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_supplier(db: AsyncSession, supplier_id: uuid.UUID) -> Supplier | None:
    result = await db.execute(
        select(Supplier).where(
            Supplier.id == supplier_id, Supplier.is_deleted.is_(False)
        )
    )
    return result.scalar_one_or_none()


async def create_supplier(
    db: AsyncSession, data: SupplierCreate, created_by: uuid.UUID
) -> Supplier:
    supplier = Supplier(**data.model_dump(), created_by=created_by)
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    return supplier


async def update_supplier(
    db: AsyncSession, supplier_id: uuid.UUID, data: SupplierUpdate
) -> Supplier | None:
    supplier = await get_supplier(db, supplier_id)
    if not supplier:
        return None
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(supplier, key, value)
    await db.commit()
    await db.refresh(supplier)
    return supplier


async def delete_supplier(db: AsyncSession, supplier_id: uuid.UUID) -> bool:
    """Soft delete."""
    supplier = await get_supplier(db, supplier_id)
    if not supplier:
        return False
    supplier.is_deleted = True
    await db.commit()
    return True
