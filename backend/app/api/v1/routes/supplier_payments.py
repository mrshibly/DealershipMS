import uuid
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.supplier_payment import SupplierPaymentCreate, SupplierPaymentRead
from app.services import supplier_payment_service

router = APIRouter(prefix="/supplier-payments", tags=["supplier-payments"])


@router.get("", response_model=PaginatedResponse[SupplierPaymentRead])
async def list_supplier_payments(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    supplier_id: uuid.UUID | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("purchases", "view")),
):
    payments, total = await supplier_payment_service.list_supplier_payments(
        db, page=page, per_page=per_page,
        supplier_id=supplier_id, date_from=date_from, date_to=date_to,
    )
    
    data = []
    for p in payments:
        data.append(SupplierPaymentRead(
            id=p.id,
            supplier_id=p.supplier_id,
            supplier_name=p.supplier.name if p.supplier else None,
            account_id=p.account_id,
            account_name=p.account.name if p.account else None,
            amount=p.amount,
            payment_date=p.payment_date,
            description=p.description,
            is_deleted=p.is_deleted,
            created_at=p.created_at,
        ))
        
    return PaginatedResponse(
        data=data, total=total, page=page,
        per_page=per_page, pages=ceil(total / per_page) if total else 0,
    )


@router.post("", response_model=SuccessResponse[SupplierPaymentRead], status_code=201)
async def create_supplier_payment(
    body: SupplierPaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("purchases", "create")),
):
    try:
        payment = await supplier_payment_service.create_supplier_payment(db, body, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
        
    return SuccessResponse(
        data=SupplierPaymentRead(
            id=payment.id,
            supplier_id=payment.supplier_id,
            amount=payment.amount,
            account_id=payment.account_id,
            payment_date=payment.payment_date,
            description=payment.description,
            is_deleted=payment.is_deleted,
            created_at=payment.created_at,
        ),
        message="Supplier payment recorded successfully"
    )


@router.post("/{id}/void", response_model=SuccessResponse[dict])
async def void_supplier_payment(
    id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("purchases", "update")),
):
    try:
        payment = await supplier_payment_service.void_supplier_payment(db, id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
        
    return SuccessResponse(
        data={"id": str(payment.id), "is_deleted": payment.is_deleted},
        message="Supplier payment voided successfully"
    )
