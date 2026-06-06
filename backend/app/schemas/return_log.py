import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ReturnLogBase(BaseModel):
    invoice_id: uuid.UUID
    product_id: uuid.UUID
    qty_returned: int = Field(..., gt=0)
    reason: str | None = Field(None, max_length=255)
    return_date: date


class ReturnLogCreate(BaseModel):
    invoice_id: uuid.UUID
    product_id: uuid.UUID
    qty_returned: int = Field(..., gt=0)
    reason: str | None = Field(None, max_length=255)
    return_date: date | None = None


class ReturnLogRead(ReturnLogBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    invoice_no: str | None = None
    product_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
