"""
Pydantic schemas for Dealer endpoints.
"""
import re
import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class DealerCreate(BaseModel):
    name: str
    owner_name: str | None = None
    phone: str
    address: str | None = None
    district: str | None = None
    upazila: str | None = None
    trade_license: str | None = None
    nid: str | None = None
    route_id: uuid.UUID | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^(\+880|0)[0-9]{10}$", v):
            raise ValueError("Phone must be a valid Bangladesh mobile number")
        return v


class DealerRead(BaseModel):
    id: uuid.UUID
    name: str
    owner_name: str | None
    phone: str
    address: str | None
    district: str | None
    upazila: str | None
    trade_license: str | None
    nid: str | None
    route_id: uuid.UUID | None
    route_name: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DealerUpdate(BaseModel):
    name: str | None = None
    owner_name: str | None = None
    phone: str | None = None
    address: str | None = None
    district: str | None = None
    upazila: str | None = None
    trade_license: str | None = None
    nid: str | None = None
    route_id: uuid.UUID | None = None
    is_active: bool | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^(\+880|0)[0-9]{10}$", v):
            raise ValueError("Phone must be a valid Bangladesh mobile number")
        return v
