"""
Collection schemas.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.collection import PaymentMethod


class CollectionBase(BaseModel):
    invoice_id: Optional[uuid.UUID] = None
    dealer_id: Optional[uuid.UUID] = None
    dsr_id: Optional[uuid.UUID] = None
    amount: Decimal = Field(..., gt=0)
    payment_method: PaymentMethod
    reference_no: Optional[str] = None
    notes: Optional[str] = None


class CollectionCreate(CollectionBase):
    pass


class CollectionRead(CollectionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    collected_at: datetime
    is_deleted: bool
    created_at: datetime


class CollectPaymentRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_method: PaymentMethod
    reference_no: Optional[str] = None
    notes: Optional[str] = None
