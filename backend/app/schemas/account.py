import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.account import AccountType


class AccountBase(BaseModel):
    name: str = Field(..., max_length=100)
    type: AccountType
    account_no: Optional[str] = Field(None, max_length=50)
    opening_balance: float = Field(0.00, ge=0)
    is_active: bool = True

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    account_no: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None

class AccountRead(AccountBase):
    id: uuid.UUID
    current_balance: float = 0.00
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
