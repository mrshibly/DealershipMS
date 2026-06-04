"""
Pydantic schemas for Inventory endpoints.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.stock_movement import MovementType


class OpeningStockCreate(BaseModel):
    product_id: uuid.UUID
    qty_pieces: int = Field(ge=1)
    unit_price: Decimal = Field(ge=Decimal("0.00"), decimal_places=2)
    movement_date: date
    notes: str | None = None


class StockAdjustmentCreate(BaseModel):
    product_id: uuid.UUID
    movement_type: MovementType
    qty_pieces: int = Field(ge=1)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    movement_date: date
    notes: str | None = None

    class Config:
        use_enum_values = True


class StockLevelRead(BaseModel):
    product_id: uuid.UUID
    product_name_en: str
    product_name_bn: str | None
    sku: str
    barcode: str | None
    pcs_per_carton: int
    unit: str
    qty_pieces: int
    qty_cartons: int
    remaining_pcs: int      # qty_pieces % pcs_per_carton
    buy_value: Decimal      # qty_pieces * buy_price
    sell_value: Decimal     # qty_pieces * sell_price
    low_stock_threshold: int
    is_low_stock: bool
    category_name: str | None

    model_config = {"from_attributes": True}


class StockMovementRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name_en: str
    movement_type: str
    qty_pieces: int
    unit_price: Decimal
    movement_date: date
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
