"""
Dealer business logic service.
"""
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dealer import Dealer
from app.schemas.dealer import DealerCreate, DealerUpdate


async def list_dealers(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    search: str | None = None,
    route_id: uuid.UUID | None = None,
    is_active: bool | None = None,
) -> tuple[list[Dealer], int]:
    query = select(Dealer).options(selectinload(Dealer.route)).where(Dealer.is_deleted.is_(False))
    if search:
        pattern = f"%{search}%"
        from sqlalchemy import or_
        query = query.where(
            or_(
                Dealer.name.ilike(pattern),
                Dealer.owner_name.ilike(pattern),
                Dealer.phone.ilike(pattern),
            )
        )
    if route_id:
        query = query.where(Dealer.route_id == route_id)
    if is_active is not None:
        query = query.where(Dealer.is_active.is_(is_active))

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar() or 0

    query = query.order_by(Dealer.name).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    dealers = result.scalars().all()

    # Enrich route_name for each dealer to fit DealerRead schema
    for dealer in dealers:
        dealer.route_name = dealer.route.name if dealer.route else None

    return list(dealers), total


async def get_dealer(db: AsyncSession, dealer_id: uuid.UUID) -> Dealer | None:
    result = await db.execute(
        select(Dealer)
        .options(selectinload(Dealer.route))
        .where(Dealer.id == dealer_id, Dealer.is_deleted.is_(False))
    )
    dealer = result.scalar_one_or_none()
    if dealer:
        dealer.route_name = dealer.route.name if dealer.route else None
    return dealer


async def create_dealer(
    db: AsyncSession, data: DealerCreate, created_by: uuid.UUID
) -> Dealer:
    # Check phone uniqueness
    existing = await db.execute(
        select(Dealer).where(Dealer.phone == data.phone, Dealer.is_deleted.is_(False))
    )
    if existing.scalar_one_or_none():
        raise ValueError(f"Dealer with phone '{data.phone}' already exists")

    dealer = Dealer(**data.model_dump(), created_by=created_by)
    db.add(dealer)
    await db.commit()
    await db.refresh(dealer, ["route"])
    dealer.route_name = dealer.route.name if dealer.route else None
    return dealer


async def update_dealer(
    db: AsyncSession, dealer_id: uuid.UUID, data: DealerUpdate
) -> Dealer | None:
    dealer = await get_dealer(db, dealer_id)
    if not dealer:
        return None

    update_data = data.model_dump(exclude_none=True)
    if "phone" in update_data and update_data["phone"] != dealer.phone:
        # Check phone uniqueness
        existing = await db.execute(
            select(Dealer).where(Dealer.phone == update_data["phone"], Dealer.is_deleted.is_(False))
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Dealer with phone '{update_data['phone']}' already exists")

    for key, value in update_data.items():
        setattr(dealer, key, value)

    await db.commit()
    await db.refresh(dealer, ["route"])
    dealer.route_name = dealer.route.name if dealer.route else None
    return dealer


async def delete_dealer(db: AsyncSession, dealer_id: uuid.UUID) -> bool:
    """Soft delete."""
    dealer = await get_dealer(db, dealer_id)
    if not dealer:
        return False
    dealer.is_deleted = True
    await db.commit()
    return True
