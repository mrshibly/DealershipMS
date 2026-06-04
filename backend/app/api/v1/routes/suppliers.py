"""
Supplier routes — CRUD.
"""
import uuid
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate
from app.services import supplier_service

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=PaginatedResponse[SupplierRead])
async def list_suppliers(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("suppliers", "view")),
):
    suppliers, total = await supplier_service.list_suppliers(
        db, page=page, per_page=per_page, search=search, is_active=is_active
    )
    return PaginatedResponse(
        data=suppliers, total=total, page=page,
        per_page=per_page, pages=ceil(total / per_page) if total else 0,
    )


@router.get("/{supplier_id}", response_model=SuccessResponse[SupplierRead])
async def get_supplier(
    supplier_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("suppliers", "view")),
):
    supplier = await supplier_service.get_supplier(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return SuccessResponse(data=supplier)


@router.post("", response_model=SuccessResponse[SupplierRead], status_code=201)
async def create_supplier(
    body: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("suppliers", "create")),
):
    supplier = await supplier_service.create_supplier(db, body, current_user.id)
    return SuccessResponse(data=supplier, message="Supplier created")


@router.put("/{supplier_id}", response_model=SuccessResponse[SupplierRead])
async def update_supplier(
    supplier_id: uuid.UUID = Path(...),
    body: SupplierUpdate = ...,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("suppliers", "update")),
):
    supplier = await supplier_service.update_supplier(db, supplier_id, body)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return SuccessResponse(data=supplier, message="Supplier updated")


@router.delete("/{supplier_id}", response_model=SuccessResponse[dict])
async def delete_supplier(
    supplier_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("suppliers", "delete")),
):
    deleted = await supplier_service.delete_supplier(db, supplier_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return SuccessResponse(data={}, message="Supplier deleted")
