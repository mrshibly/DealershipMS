"""
DSR business logic service.
"""
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dsr import DSR
from app.schemas.dsr import DSRCreate, DSRUpdate


async def list_dsrs(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    search: str | None = None,
    route_id: uuid.UUID | None = None,
    is_active: bool | None = None,
) -> tuple[list[DSR], int]:
    query = select(DSR).options(selectinload(DSR.route)).where(DSR.is_deleted.is_(False))
    if search:
        pattern = f"%{search}%"
        from sqlalchemy import or_
        query = query.where(
            or_(
                DSR.name.ilike(pattern),
                DSR.phone.ilike(pattern),
                DSR.nid.ilike(pattern),
            )
        )
    if route_id:
        query = query.where(DSR.route_id == route_id)
    if is_active is not None:
        query = query.where(DSR.is_active.is_(is_active))

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar() or 0

    query = query.order_by(DSR.name).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    dsrs = result.scalars().all()

    # Enrich route_name for each DSR to fit DSRRead schema
    for dsr in dsrs:
        dsr.route_name = dsr.route.name if dsr.route else None

    return list(dsrs), total


async def get_dsr(db: AsyncSession, dsr_id: uuid.UUID) -> DSR | None:
    result = await db.execute(
        select(DSR)
        .options(selectinload(DSR.route))
        .where(DSR.id == dsr_id, DSR.is_deleted.is_(False))
    )
    dsr = result.scalar_one_or_none()
    if dsr:
        dsr.route_name = dsr.route.name if dsr.route else None
    return dsr


async def create_dsr(
    db: AsyncSession, data: DSRCreate, created_by: uuid.UUID
) -> DSR:
    # Check phone uniqueness
    existing = await db.execute(
        select(DSR).where(DSR.phone == data.phone, DSR.is_deleted.is_(False))
    )
    if existing.scalar_one_or_none():
        raise ValueError(f"DSR with phone '{data.phone}' already exists")

    dsr = DSR(**data.model_dump(), created_by=created_by)
    db.add(dsr)
    await db.commit()
    await db.refresh(dsr, ["route"])
    dsr.route_name = dsr.route.name if dsr.route else None
    return dsr


async def update_dsr(
    db: AsyncSession, dsr_id: uuid.UUID, data: DSRUpdate
) -> DSR | None:
    dsr = await get_dsr(db, dsr_id)
    if not dsr:
        return None

    update_data = data.model_dump(exclude_none=True)
    if "phone" in update_data and update_data["phone"] != dsr.phone:
        # Check phone uniqueness
        existing = await db.execute(
            select(DSR).where(DSR.phone == update_data["phone"], DSR.is_deleted.is_(False))
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"DSR with phone '{update_data['phone']}' already exists")

    for key, value in update_data.items():
        setattr(dsr, key, value)

    await db.commit()
    await db.refresh(dsr, ["route"])
    dsr.route_name = dsr.route.name if dsr.route else None
    return dsr


async def delete_dsr(db: AsyncSession, dsr_id: uuid.UUID) -> bool:
    """Soft delete."""
    dsr = await get_dsr(db, dsr_id)
    if not dsr:
        return False
    dsr.is_deleted = True
    await db.commit()
    return True
