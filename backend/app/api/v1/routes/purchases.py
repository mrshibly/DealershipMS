"""
Purchase routes — CRUD + receive + cancel.
"""
import uuid
from decimal import Decimal
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.purchase import PurchaseCreate, PurchaseRead, PurchaseUpdate
from app.services import purchase_service

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.get("", response_model=PaginatedResponse[PurchaseRead])
async def list_purchases(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    supplier_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("purchases", "view")),
):
    purchases, total = await purchase_service.list_purchases(
        db, page=page, per_page=per_page,
        supplier_id=supplier_id, status=status,
        date_from=date_from, date_to=date_to,
    )
    data = []
    for p in purchases:
        d = {c.name: getattr(p, c.name) for c in p.__table__.columns}
        d["supplier_name"] = p.supplier.name if p.supplier else None
        d["items"] = []
        d["status"] = p.status.value if hasattr(p.status, "value") else p.status
        data.append(d)
    return PaginatedResponse(
        data=data, total=total, page=page,
        per_page=per_page, pages=ceil(total / per_page) if total else 0,
    )


@router.get("/{purchase_id}", response_model=SuccessResponse[PurchaseRead])
async def get_purchase(
    purchase_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("purchases", "view")),
):
    purchase = await purchase_service.get_purchase(db, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    data = {c.name: getattr(purchase, c.name) for c in purchase.__table__.columns}
    data["supplier_name"] = purchase.supplier.name if purchase.supplier else None
    data["status"] = purchase.status.value if hasattr(purchase.status, "value") else purchase.status
    data["items"] = [
        {
            "id": item.id,
            "product_id": item.product_id,
            "product_name_en": item.product.name_en if item.product else "",
            "product_sku": item.product.sku if item.product else "",
            "qty_carton": item.qty_carton,
            "qty_pcs": item.qty_pcs,
            "total_pieces": item.total_pieces,
            "buy_price": item.buy_price,
            "line_total": item.line_total,
        }
        for item in purchase.items
    ]
    return SuccessResponse(data=data)


@router.post("", response_model=SuccessResponse[PurchaseRead], status_code=201)
async def create_purchase(
    body: PurchaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("purchases", "create")),
):
    try:
        purchase = await purchase_service.create_purchase(db, body, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    data = {c.name: getattr(purchase, c.name) for c in purchase.__table__.columns}
    data["supplier_name"] = None
    data["status"] = purchase.status.value
    data["items"] = []
    return SuccessResponse(data=data, message="Purchase created as DRAFT")


@router.post("/{purchase_id}/receive", response_model=SuccessResponse[dict])
async def receive_purchase(
    purchase_id: uuid.UUID = Path(...),
    paid: Decimal = Query(default=Decimal("0.00"), ge=Decimal("0")),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("purchases", "update")),
):
    """
    Mark purchase as RECEIVED. Creates stock_movements atomically.
    INSTRUCTION.md §7: single DB transaction.
    """
    try:
        purchase = await purchase_service.receive_purchase(db, purchase_id, paid, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return SuccessResponse(
        data={"purchase_id": str(purchase.id), "status": purchase.status.value},
        message="Purchase received. Stock updated.",
    )


@router.post("/{purchase_id}/cancel", response_model=SuccessResponse[dict])
async def cancel_purchase(
    purchase_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("purchases", "update")),
):
    try:
        purchase = await purchase_service.cancel_purchase(db, purchase_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return SuccessResponse(
        data={"status": purchase.status.value},
        message="Purchase cancelled",
    )
