import uuid
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.purchase_return import PurchaseReturnCreate, PurchaseReturnRead, PurchaseReturnItemRead
from app.services import purchase_return_service

router = APIRouter(prefix="/purchase-returns", tags=["purchase-returns"])


@router.get("", response_model=PaginatedResponse[PurchaseReturnRead])
async def list_purchase_returns(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    supplier_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("purchases", "view")),
):
    returns, total = await purchase_return_service.list_purchase_returns(
        db, page=page, per_page=per_page,
        supplier_id=supplier_id, status=status,
    )
    
    data = []
    for r in returns:
        data.append(PurchaseReturnRead(
            id=r.id,
            supplier_id=r.supplier_id,
            supplier_name=r.supplier.name if r.supplier else None,
            purchase_id=r.purchase_id,
            purchase_no=r.purchase.invoice_no if r.purchase else None,
            return_no=r.return_no,
            return_date=r.return_date,
            subtotal=r.subtotal,
            discount=r.discount,
            vat_amount=r.vat_amount,
            total_receivable=r.total_receivable,
            status=r.status.value,
            notes=r.notes,
            created_at=r.created_at,
        ))
        
    return PaginatedResponse(
        data=data, total=total, page=page,
        per_page=per_page, pages=ceil(total / per_page) if total else 0,
    )


@router.get("/{id}", response_model=SuccessResponse[PurchaseReturnRead])
async def get_purchase_return(
    id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("purchases", "view")),
):
    r = await purchase_return_service.get_purchase_return_detail(db, id)
    if not r:
        raise HTTPException(status_code=404, detail="Purchase return not found")
        
    items = []
    for item in r.items:
        items.append(PurchaseReturnItemRead(
            id=item.id,
            product_id=item.product_id,
            product_name_en=item.product.name_en if item.product else "",
            product_name_bn=item.product.name_bn if item.product else None,
            qty_carton=item.qty_carton,
            qty_pcs=item.qty_pcs,
            total_pieces=item.total_pieces,
            return_price=item.return_price,
            line_total=item.line_total,
        ))
        
    data = PurchaseReturnRead(
        id=r.id,
        supplier_id=r.supplier_id,
        supplier_name=r.supplier.name if r.supplier else None,
        purchase_id=r.purchase_id,
        purchase_no=r.purchase.invoice_no if r.purchase else None,
        return_no=r.return_no,
        return_date=r.return_date,
        subtotal=r.subtotal,
        discount=r.discount,
        vat_amount=r.vat_amount,
        total_receivable=r.total_receivable,
        status=r.status.value,
        notes=r.notes,
        items=items,
        created_at=r.created_at,
    )
    return SuccessResponse(data=data)


@router.post("", response_model=SuccessResponse[PurchaseReturnRead], status_code=201)
async def create_purchase_return(
    body: PurchaseReturnCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("purchases", "create")),
):
    try:
        r = await purchase_return_service.create_purchase_return(db, body, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
        
    return SuccessResponse(
        data=PurchaseReturnRead(
            id=r.id,
            supplier_id=r.supplier_id,
            purchase_id=r.purchase_id,
            return_no=r.return_no,
            return_date=r.return_date,
            subtotal=r.subtotal,
            discount=r.discount,
            vat_amount=r.vat_amount,
            total_receivable=r.total_receivable,
            status=r.status.value,
            notes=r.notes,
            created_at=r.created_at,
        ),
        message="Purchase return created as DRAFT"
    )


@router.post("/{id}/confirm", response_model=SuccessResponse[dict])
async def confirm_purchase_return(
    id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("purchases", "update")),
):
    try:
        r = await purchase_return_service.confirm_purchase_return(db, id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
        
    return SuccessResponse(
        data={"id": str(r.id), "status": r.status.value},
        message="Purchase return confirmed. Inventory updated."
    )


@router.post("/{id}/void", response_model=SuccessResponse[dict])
async def void_purchase_return(
    id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("purchases", "update")),
):
    try:
        r = await purchase_return_service.void_purchase_return(db, id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
        
    return SuccessResponse(
        data={"id": str(r.id), "is_deleted": True},
        message="Purchase return voided successfully"
    )
