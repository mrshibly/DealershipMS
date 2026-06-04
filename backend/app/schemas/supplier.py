"""
Pydantic schemas for Supplier endpoints.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator
import re


class SupplierCreate(BaseModel):
    name: str
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    district: str | None = None
    vat_no: str | None = None
    bank_name: str | None = None
    bank_account: str | None = None
    opening_balance: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^(\+880|0)[0-9]{10}$", v):
            raise ValueError("Phone must be a valid Bangladesh mobile number")
        return v


class SupplierRead(BaseModel):
    id: uuid.UUID
    name: str
    contact_person: str | None
    phone: str | None
    email: str | None
    address: str | None
    district: str | None
    vat_no: str | None
    opening_balance: Decimal
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SupplierUpdate(BaseModel):
    name: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    district: str | None = None
    vat_no: str | None = None
    bank_name: str | None = None
    bank_account: str | None = None
    is_active: bool | None = None
