"""
Product routes — CRUD + barcode generation.
All routes require JWT + RBAC.
"""
import uuid
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.product import (
    CategoryCreate, CategoryRead, CategoryUpdate,
    ProductCreate, ProductRead, ProductUpdate,
)
from app.services import product_service
from app.utils.barcode import generate_barcode_png

router = APIRouter(prefix="/products", tags=["products"])
cat_router = APIRouter(prefix="/categories", tags=["categories"])


# ── Categories ────────────────────────────────────────────────────────────────

@cat_router.get("", response_model=SuccessResponse[list[CategoryRead]])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("products", "view")),
):
    cats = await product_service.list_categories(db)
    return SuccessResponse(data=cats)


@cat_router.post("", response_model=SuccessResponse[CategoryRead], status_code=201)
async def create_category(
    body: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("products", "create")),
):
    cat = await product_service.create_category(db, body.model_dump(), current_user.id)
    return SuccessResponse(data=cat, message="Category created")


# ── Products ──────────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedResponse[ProductRead])
async def list_products(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    category_id: uuid.UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("products", "view")),
):
    products, total = await product_service.list_products(
        db, page=page, per_page=per_page,
        search=search, category_id=category_id, is_active=is_active,
    )
    return PaginatedResponse(
        data=products, total=total, page=page,
        per_page=per_page, pages=ceil(total / per_page) if total else 0,
    )


@router.get("/{product_id}", response_model=SuccessResponse[ProductRead])
async def get_product(
    product_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("products", "view")),
):
    product = await product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    enriched = await product_service._enrich_product(db, product)
    return SuccessResponse(data=enriched)


@router.post("", response_model=SuccessResponse[ProductRead], status_code=201)
async def create_product(
    body: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("products", "create")),
):
    try:
        product = await product_service.create_product(db, body, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return SuccessResponse(data=product, message="Product created")


@router.put("/{product_id}", response_model=SuccessResponse[ProductRead])
async def update_product(
    product_id: uuid.UUID = Path(...),
    body: ProductUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("products", "update")),
):
    product = await product_service.update_product(db, product_id, body, current_user.id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return SuccessResponse(data=product, message="Product updated")


@router.delete("/{product_id}", response_model=SuccessResponse[dict])
async def delete_product(
    product_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("products", "delete")),
):
    deleted = await product_service.delete_product(db, product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    return SuccessResponse(data={}, message="Product deleted")


@router.get("/{product_id}/barcode", summary="Download barcode PNG for a product")
async def get_barcode(
    product_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("products", "view")),
):
    product = await product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not product.barcode:
        raise HTTPException(status_code=404, detail="Product has no barcode assigned")

    png_bytes = generate_barcode_png(product.barcode)
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{product.sku}.png"'},
    )
