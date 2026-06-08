"""
Invoice routes.
"""
import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import Response

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


@router.put("/{id}", response_model=SuccessResponse[InvoiceDetailRead])
async def update_invoice(
    id: uuid.UUID = Path(...),
    data: InvoiceCreate = ...,
    db = Depends(get_db),
    current_user: User = Depends(require_permission("invoices", "update"))
):
    """Update/Adjust a draft invoice"""
    invoice = await invoice_service.update_invoice(db, id, data, current_user.id)
    return SuccessResponse(data=invoice, message="Invoice adjusted successfully")


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


@router.get("/{id}/pdf", summary="Download invoice as PDF")
async def download_invoice_pdf(
    id: uuid.UUID = Path(...),
    db = Depends(get_db),
    current_user: User = Depends(require_permission("invoices", "read"))
):
    """Generate and download an NBR-compliant PDF for the invoice"""
    from app.utils.pdf import generate_invoice_pdf
    from app.core.config import get_settings
    invoice = await invoice_service.get_invoice_detail(db, id)
    settings = get_settings()

    # Build the data dict for the PDF generator
    data = {
        "invoice_no": invoice.invoice_no,
        "date": str(invoice.date),
        "status": invoice.status.value,
        "dealer_name": invoice.dealer.name if invoice.dealer else "-",
        "dealer_address": invoice.dealer.address if invoice.dealer else "",
        "dealer_phone": invoice.dealer.phone if invoice.dealer else "",
        "dsr_name": invoice.dsr.name if invoice.dsr else "-",
        "shop_name": invoice.shop.name if invoice.shop else "-",
        "items": [
            {
                "name": item.product.name_en if item.product else str(item.product_id),
                "total_pieces": item.total_pieces,
                "unit_price": item.unit_price,
                "vat_rate": item.vat_rate,
                "vat_amount": item.vat_amount,
                "line_total": item.line_total,
                "is_free_item": item.is_free_item,
            }
            for item in invoice.items
        ],
        "subtotal": invoice.subtotal,
        "discount": invoice.discount,
        "vat_amount": invoice.vat_amount,
        "grand_total": invoice.grand_total,
        "paid_amount": invoice.paid_amount,
        "company_name": settings.company_name,
        "company_address": settings.company_address,
        "company_phone": settings.company_phone,
        "company_vat_bin": settings.company_vat_bin,
    }

    pdf_bytes = generate_invoice_pdf(data)
    filename = f"invoice-{invoice.invoice_no}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
