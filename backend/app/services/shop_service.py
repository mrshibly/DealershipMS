"""
Shop business logic service.
"""
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.shop import Shop
from app.schemas.shop import ShopCreate, ShopUpdate


async def list_shops(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    search: str | None = None,
    dealer_id: uuid.UUID | None = None,
    is_active: bool | None = None,
) -> tuple[list[Shop], int]:
    query = select(Shop).options(selectinload(Shop.dealer)).where(Shop.is_deleted.is_(False))
    if search:
        pattern = f"%{search}%"
        from sqlalchemy import or_
        query = query.where(
            or_(
                Shop.name.ilike(pattern),
                Shop.owner_name.ilike(pattern),
            )
        )
    if dealer_id:
        query = query.where(Shop.dealer_id == dealer_id)
    if is_active is not None:
        query = query.where(Shop.is_active.is_(is_active))

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar() or 0

    query = query.order_by(Shop.name).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    shops = result.scalars().all()

    # Enrich dealer_name for each shop to fit ShopRead schema
    for shop in shops:
        shop.dealer_name = shop.dealer.name if shop.dealer else None

    return list(shops), total


async def get_shop(db: AsyncSession, shop_id: uuid.UUID) -> Shop | None:
    result = await db.execute(
        select(Shop)
        .options(selectinload(Shop.dealer))
        .where(Shop.id == shop_id, Shop.is_deleted.is_(False))
    )
    shop = result.scalar_one_or_none()
    if shop:
        shop.dealer_name = shop.dealer.name if shop.dealer else None
    return shop


async def create_shop(
    db: AsyncSession, data: ShopCreate, created_by: uuid.UUID
) -> Shop:
    shop = Shop(**data.model_dump(), created_by=created_by)
    db.add(shop)
    await db.commit()
    await db.refresh(shop, ["dealer"])
    shop.dealer_name = shop.dealer.name if shop.dealer else None
    return shop


async def update_shop(
    db: AsyncSession, shop_id: uuid.UUID, data: ShopUpdate
) -> Shop | None:
    shop = await get_shop(db, shop_id)
    if not shop:
        return None

    update_data = data.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(shop, key, value)

    await db.commit()
    await db.refresh(shop, ["dealer"])
    shop.dealer_name = shop.dealer.name if shop.dealer else None
    return shop


async def delete_shop(db: AsyncSession, shop_id: uuid.UUID) -> bool:
    """Soft delete."""
    shop = await get_shop(db, shop_id)
    if not shop:
        return False
    shop.is_deleted = True
    await db.commit()
    return True


async def list_shops_by_dealer(db: AsyncSession, dealer_id: uuid.UUID) -> list[Shop]:
    result = await db.execute(
        select(Shop)
        .options(selectinload(Shop.dealer))
        .where(Shop.dealer_id == dealer_id, Shop.is_deleted.is_(False))
        .order_by(Shop.name)
    )
    shops = result.scalars().all()
    for shop in shops:
        shop.dealer_name = shop.dealer.name if shop.dealer else None
    return list(shops)
