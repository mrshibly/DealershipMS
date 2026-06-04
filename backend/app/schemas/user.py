"""
Pydantic schemas for User endpoints.
password_hash is NEVER included in any response schema.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserRead(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role_id: uuid.UUID | None
    language: str
    phone: str | None
    is_active: bool
    created_at: datetime
    last_login: datetime | None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role_id: uuid.UUID | None = None
    language: str = "bn"
    phone: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_bd_phone(cls, v: str | None) -> str | None:
        import re
        if v is None:
            return v
        pattern = r"^(\+880|0)[0-9]{10}$"
        if not re.match(pattern, v):
            raise ValueError("Phone must be a valid Bangladesh mobile number (+880XXXXXXXXXX or 0XXXXXXXXXX)")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in ("bn", "en", "hi", "ar"):
            raise ValueError("Language must be one of: bn, en, hi, ar")
        return v


class UserUpdate(BaseModel):
    name: str | None = None
    language: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    role_id: uuid.UUID | None = None

    @field_validator("phone")
    @classmethod
    def validate_bd_phone(cls, v: str | None) -> str | None:
        import re
        if v is None:
            return v
        pattern = r"^(\+880|0)[0-9]{10}$"
        if not re.match(pattern, v):
            raise ValueError("Phone must be a valid Bangladesh mobile number")
        return v


class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
