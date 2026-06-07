"""
Collections router.
"""
import uuid
from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import require_permission
from app.models.collection import Collection
from app.schemas.common import PaginatedResponse
from app.schemas.collection import CollectionRead

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("", response_model=PaginatedResponse[CollectionRead])
async def list_collections(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    dealer_id: Optional[uuid.UUID] = None,
    dsr_id: Optional[uuid.UUID] = None,
    invoice_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("invoices", "read")),
):
    query = select(Collection).where(Collection.is_deleted == False)
    if dealer_id:
        query = query.where(Collection.dealer_id == dealer_id)
    if dsr_id:
        query = query.where(Collection.dsr_id == dsr_id)
    if invoice_id:
        query = query.where(Collection.invoice_id == invoice_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    # Paginate and fetch
    query = (
        query.options(
            selectinload(Collection.invoice),
            selectinload(Collection.dealer),
            selectinload(Collection.dsr),
            selectinload(Collection.account),
        )
        .order_by(Collection.collected_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    res = await db.execute(query)
    collections = res.scalars().all()

    # Enrich response models with names
    enriched_collections = []
    for c in collections:
        read_obj = CollectionRead.model_validate(c)
        read_obj.invoice_no = c.invoice.invoice_no if c.invoice else None
        read_obj.dealer_name = c.dealer.name if c.dealer else None
        read_obj.dsr_name = c.dsr.name if c.dsr else None
        read_obj.account_name = c.account.name if c.account else None
        enriched_collections.append(read_obj)

    return PaginatedResponse(
        data=enriched_collections,
        total=total,
        page=page,
        per_page=per_page,
        pages=ceil(total / per_page) if total else 0,
    )
