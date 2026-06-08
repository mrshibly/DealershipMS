import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class SupplierPaymentCreate(BaseModel):
    supplier_id: uuid.UUID
    account_id: uuid.UUID
    amount: Decimal = Field(gt=Decimal("0.00"), decimal_places=2)
    payment_date: date = Field(default_factory=date.today)
    description: str | None = None


class SupplierPaymentRead(BaseModel):
    id: uuid.UUID
    supplier_id: uuid.UUID
    supplier_name: str | None = None
    account_id: uuid.UUID
    account_name: str | None = None
    amount: Decimal
    payment_date: date
    description: str | None = None
    is_deleted: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
