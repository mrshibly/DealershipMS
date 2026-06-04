"""
Invoice routes.
"""
import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, Path

from app.core.database import get_db
from app.core.security import require_permission, get_current_user
from app.models.invoice import InvoiceStatus
from app.models.user import User
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.invoice import (
    InvoiceCreate, InvoiceDetailRead, InvoiceRead
)
from app.schemas.collection import CollectPaymentRequest
from app.services import invoice_service

router = APIRouter(prefix="/invoices", tags=["invoices"])

# Note: Using InvoiceRead for List to avoid recursive circular references in list
# But creating InvoiceListRead just in case we need smaller payload

@router.post("", response_model=SuccessResponse[InvoiceDetailRead])
async def create_invoice(
    data: InvoiceCreate,
    db = Depends(get_db),
    current_user: User = Depends(require_permission("invoices", "create"))
):
    """Create a new invoice (saved as DRAFT initially)"""
    invoice = await invoice_service.create_invoice(db, data, current_user.id)
    return SuccessResponse(data=invoice)


@router.get("", response_model=PaginatedResponse[InvoiceRead])
async def list_invoices(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    dealer_id: Optional[uuid.UUID] = None,
    dsr_id: Optional[uuid.UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status: Optional[InvoiceStatus] = None,
    db = Depends(get_db),
    current_user: User = Depends(require_permission("invoices", "read"))
):
    """List invoices with pagination and filters"""
    result = await invoice_service.list_invoices(
        db, page, per_page, dealer_id, dsr_id, date_from, date_to, status
    )
    return PaginatedResponse(**result)


@router.get("/{id}", response_model=SuccessResponse[InvoiceDetailRead])
async def get_invoice(
    id: uuid.UUID = Path(...),
    db = Depends(get_db),
    current_user: User = Depends(require_permission("invoices", "read"))
):
    """Get full invoice details including items and collections"""
    invoice = await invoice_service.get_invoice_detail(db, id)
    return SuccessResponse(data=invoice)


@router.post("/{id}/confirm", response_model=SuccessResponse[InvoiceDetailRead])
async def confirm_invoice(
    id: uuid.UUID = Path(...),
    db = Depends(get_db),
    current_user: User = Depends(require_permission("invoices", "update"))
):
    """Confirm an invoice (deducts stock, updates status)"""
    invoice = await invoice_service.confirm_invoice(db, id, current_user.id)
    return SuccessResponse(data=invoice)


@router.post("/{id}/collect", response_model=SuccessResponse[InvoiceDetailRead])
async def collect_payment(
    data: CollectPaymentRequest,
    id: uuid.UUID = Path(...),
    db = Depends(get_db),
    current_user: User = Depends(require_permission("invoices", "update"))
):
    """Record a payment collection against an invoice"""
    invoice = await invoice_service.collect_payment(db, id, data, current_user.id)
    return SuccessResponse(data=invoice)


@router.post("/{id}/void", response_model=SuccessResponse[InvoiceDetailRead])
async def void_invoice(
    id: uuid.UUID = Path(...),
    db = Depends(get_db),
    current_user: User = Depends(require_permission("invoices", "delete"))
):
    """Void an invoice (soft delete + reverse stock if confirmed)"""
    invoice = await invoice_service.void_invoice(db, id, current_user.id)
    return SuccessResponse(data=invoice)
