"""
Invoice schemas.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.invoice import InvoiceStatus
from app.schemas.collection import CollectionRead
from app.schemas.product import ProductRead
from app.schemas.dealer import DealerRead
from app.schemas.dsr import DSRRead
from app.schemas.shop import ShopRead


class InvoiceItemBase(BaseModel):
    product_id: uuid.UUID
    qty_carton: int = Field(ge=0, default=0)
    qty_pcs: int = Field(ge=0, default=0)
    is_free_item: bool = False


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemRead(InvoiceItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    total_pieces: int
    unit_price: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    discount: Decimal
    line_total: Decimal
    product: Optional[ProductRead] = None


class InvoiceBase(BaseModel):
    dealer_id: Optional[uuid.UUID] = None
    dsr_id: Optional[uuid.UUID] = None
    shop_id: Optional[uuid.UUID] = None
    date: date
    discount: Decimal = Field(default=Decimal("0.00"), ge=0)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    items: list[InvoiceItemCreate] = Field(min_length=1)
    
    # Optionally, a payment can be made at the time of creation
    payment_method: Optional[str] = None
    payment_amount: Optional[Decimal] = Field(default=None, ge=0)
    payment_reference: Optional[str] = None


class InvoiceRead(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_no: str
    subtotal: Decimal
    vat_amount: Decimal
    grand_total: Decimal
    paid_amount: Decimal
    status: InvoiceStatus
    is_deleted: bool
    created_at: datetime
    dealer_name: Optional[str] = None
    dsr_name: Optional[str] = None
    route_name: Optional[str] = None


class InvoiceDetailRead(InvoiceRead):
    items: list[InvoiceItemRead]
    collections: list[CollectionRead]
    dealer: Optional[DealerRead] = None
    dsr: Optional[DSRRead] = None
    shop: Optional[ShopRead] = None
