"""
Route business logic service.
"""
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.route import Route
from app.schemas.route import RouteCreate, RouteUpdate


async def list_routes(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    search: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[Route], int]:
    query = select(Route).where(Route.is_deleted.is_(False))
    if search:
        pattern = f"%{search}%"
        from sqlalchemy import or_
        query = query.where(
            or_(
                Route.name.ilike(pattern),
                Route.area.ilike(pattern),
                Route.description.ilike(pattern),
            )
        )
    if is_active is not None:
        query = query.where(Route.is_active.is_(is_active))

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar() or 0

    query = query.order_by(Route.name).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_route(db: AsyncSession, route_id: uuid.UUID) -> Route | None:
    result = await db.execute(
        select(Route).where(
            Route.id == route_id, Route.is_deleted.is_(False)
        )
    )
    return result.scalar_one_or_none()


async def create_route(
    db: AsyncSession, data: RouteCreate, created_by: uuid.UUID
) -> Route:
    route = Route(**data.model_dump(), created_by=created_by)
    db.add(route)
    await db.commit()
    await db.refresh(route)
    return route


async def update_route(
    db: AsyncSession, route_id: uuid.UUID, data: RouteUpdate
) -> Route | None:
    route = await get_route(db, route_id)
    if not route:
        return None
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(route, key, value)
    await db.commit()
    await db.refresh(route)
    return route


async def delete_route(db: AsyncSession, route_id: uuid.UUID) -> bool:
    """Soft delete."""
    route = await get_route(db, route_id)
    if not route:
        return False
    route.is_deleted = True
    await db.commit()
    return True
