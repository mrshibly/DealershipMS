"""
Pydantic schemas for Purchase endpoints.
All monetary fields use Decimal.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class PurchaseItemCreate(BaseModel):
    product_id: uuid.UUID
    qty_carton: int = Field(default=0, ge=0)
    qty_pcs: int = Field(default=0, ge=0)
    buy_price: Decimal = Field(ge=Decimal("0.00"), decimal_places=2)

    @model_validator(mode="after")
    def at_least_one_qty(self) -> "PurchaseItemCreate":
        if self.qty_carton == 0 and self.qty_pcs == 0:
            raise ValueError("At least one of qty_carton or qty_pcs must be > 0")
        return self


class PurchaseItemRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name_en: str
    product_sku: str
    qty_carton: int
    qty_pcs: int
    total_pieces: int
    buy_price: Decimal
    line_total: Decimal

    model_config = {"from_attributes": True}


class PurchaseCreate(BaseModel):
    supplier_id: uuid.UUID | None = None
    purchase_date: date
    invoice_no: str | None = None
    discount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    notes: str | None = None
    items: list[PurchaseItemCreate] = Field(min_length=1)


class PurchaseRead(BaseModel):
    id: uuid.UUID
    supplier_id: uuid.UUID | None
    supplier_name: str | None = None
    purchase_date: date
    invoice_no: str | None
    subtotal: Decimal
    vat_amount: Decimal
    discount: Decimal
    total: Decimal
    paid: Decimal
    status: str
    notes: str | None
    items: list[PurchaseItemRead] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class PurchaseUpdate(BaseModel):
    supplier_id: uuid.UUID | None = None
    purchase_date: date | None = None
    invoice_no: str | None = None
    discount: Decimal | None = None
    notes: str | None = None
    paid: Decimal | None = Field(default=None, ge=Decimal("0.00"))
