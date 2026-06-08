import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class PurchaseReturnItemCreate(BaseModel):
    product_id: uuid.UUID
    qty_carton: int = Field(default=0, ge=0)
    qty_pcs: int = Field(default=0, ge=0)
    return_price: Decimal = Field(gt=Decimal("0.00"), decimal_places=2)


class PurchaseReturnItemRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name_en: str | None = None
    product_name_bn: str | None = None
    qty_carton: int
    qty_pcs: int
    total_pieces: int
    return_price: Decimal
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class PurchaseReturnCreate(BaseModel):
    supplier_id: uuid.UUID
    purchase_id: uuid.UUID | None = None
    return_date: date = Field(default_factory=date.today)
    discount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    notes: str | None = None
    items: list[PurchaseReturnItemCreate]


class PurchaseReturnRead(BaseModel):
    id: uuid.UUID
    supplier_id: uuid.UUID
    supplier_name: str | None = None
    purchase_id: uuid.UUID | None = None
    purchase_no: str | None = None
    return_no: str
    return_date: date
    subtotal: Decimal
    discount: Decimal
    vat_amount: Decimal
    total_receivable: Decimal
    status: str
    notes: str | None = None
    items: list[PurchaseReturnItemRead] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
