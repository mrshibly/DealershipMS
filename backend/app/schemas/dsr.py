"""
Pydantic schemas for DSR endpoints.
"""
import re
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class DSRCreate(BaseModel):
    name: str
    phone: str
    nid: str | None = None
    photo: str | None = None
    route_id: uuid.UUID | None = None
    commission_rate: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), le=Decimal("100.00"), decimal_places=2)
    joining_date: date | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^(\+880|0)[0-9]{10}$", v):
            raise ValueError("Phone must be a valid Bangladesh mobile number")
        return v

    @field_validator("commission_rate", mode="before")
    @classmethod
    def coerce_decimal(cls, v) -> Decimal:
        return Decimal(str(v))


class DSRRead(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    nid: str | None
    photo: str | None
    route_id: uuid.UUID | None
    route_name: str | None = None
    commission_rate: Decimal
    joining_date: date | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DSRUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    nid: str | None = None
    photo: str | None = None
    route_id: uuid.UUID | None = None
    commission_rate: Decimal | None = Field(default=None, ge=Decimal("0.00"), le=Decimal("100.00"))
    joining_date: date | None = None
    is_active: bool | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^(\+880|0)[0-9]{10}$", v):
            raise ValueError("Phone must be a valid Bangladesh mobile number")
        return v

    @field_validator("commission_rate", mode="before")
    @classmethod
    def coerce_decimal(cls, v) -> Decimal | None:
        if v is None:
            return None
        return Decimal(str(v))
