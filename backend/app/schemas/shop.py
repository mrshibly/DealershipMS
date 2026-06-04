"""
Pydantic schemas for Shop endpoints.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class ShopCreate(BaseModel):
    dealer_id: uuid.UUID | None = None
    name: str
    owner_name: str | None = None
    address: str | None = None
    shop_type: str = "Retailer"

    @field_validator("shop_type")
    @classmethod
    def validate_shop_type(cls, v: str) -> str:
        allowed = {"Retailer", "Wholesaler"}
        if v not in allowed:
            raise ValueError("shop_type must be either Retailer or Wholesaler")
        return v


class ShopRead(BaseModel):
    id: uuid.UUID
    dealer_id: uuid.UUID | None
    dealer_name: str | None = None
    name: str
    owner_name: str | None
    address: str | None
    shop_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShopUpdate(BaseModel):
    dealer_id: uuid.UUID | None = None
    name: str | None = None
    owner_name: str | None = None
    address: str | None = None
    shop_type: str | None = None
    is_active: bool | None = None

    @field_validator("shop_type")
    @classmethod
    def validate_shop_type(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"Retailer", "Wholesaler"}
        if v not in allowed:
            raise ValueError("shop_type must be either Retailer or Wholesaler")
        return v
