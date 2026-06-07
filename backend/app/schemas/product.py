"""
Pydantic schemas for Product and Category endpoints.
All monetary fields use Decimal, never float.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


# ── Category ──────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str
    name_bn: str | None = None
    description: str | None = None


class CategoryRead(BaseModel):
    id: uuid.UUID
    name: str
    name_bn: str | None
    description: str | None
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class CategoryUpdate(BaseModel):
    name: str | None = None
    name_bn: str | None = None
    description: str | None = None
    is_active: bool | None = None


# ── Product ───────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name_en: str
    name_bn: str | None = None
    brand: str | None = None
    sku: str | None = None              # Auto-generated if not provided
    category_id: uuid.UUID | None = None
    unit: str = "piece"
    pcs_per_carton: int = Field(default=1, ge=1)
    buy_price: Decimal = Field(ge=Decimal("0.00"), decimal_places=2)
    sell_price: Decimal = Field(ge=Decimal("0.00"), decimal_places=2)
    mrp: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    vat_applicable: bool = True
    vat_rate: Decimal = Field(default=Decimal("15.00"), ge=Decimal("0"), le=Decimal("100"))
    low_stock_threshold: int = Field(default=0, ge=0)
    description: str | None = None

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        allowed = {"piece", "kg", "litre", "set", "box", "pack"}
        if v not in allowed:
            raise ValueError(f"unit must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("buy_price", "sell_price", mode="before")
    @classmethod
    def coerce_decimal(cls, v) -> Decimal:
        return Decimal(str(v))


class ProductRead(BaseModel):
    id: uuid.UUID
    name_en: str
    name_bn: str | None
    brand: str | None = None
    sku: str
    barcode: str | None
    category_id: uuid.UUID | None
    category_name: str | None = None
    unit: str
    pcs_per_carton: int
    buy_price: Decimal
    sell_price: Decimal
    mrp: Decimal | None
    vat_applicable: bool
    vat_rate: Decimal
    low_stock_threshold: int
    description: str | None
    is_active: bool
    created_at: datetime
    # Computed at query time
    stock_qty_pieces: int = 0
    stock_qty_cartons: int = 0
    is_low_stock: bool = False

    model_config = {"from_attributes": True}


class ProductUpdate(BaseModel):
    name_en: str | None = None
    name_bn: str | None = None
    brand: str | None = None
    category_id: uuid.UUID | None = None
    unit: str | None = None
    pcs_per_carton: int | None = Field(default=None, ge=1)
    buy_price: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    sell_price: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    mrp: Decimal | None = None
    vat_applicable: bool | None = None
    vat_rate: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("100"))
    low_stock_threshold: int | None = Field(default=None, ge=0)
    description: str | None = None
    is_active: bool | None = None
