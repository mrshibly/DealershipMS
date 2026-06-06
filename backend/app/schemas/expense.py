import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

class ExpenseHeadBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    is_active: bool = True

class ExpenseHeadCreate(ExpenseHeadBase):
    pass

class ExpenseHeadUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ExpenseHeadRead(ExpenseHeadBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExpenseBase(BaseModel):
    head_id: uuid.UUID
    amount: float = Field(..., gt=0)
    date: date
    account_id: uuid.UUID
    description: Optional[str] = None
    reference: Optional[str] = Field(None, max_length=100)

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseRead(ExpenseBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    # Enrichment
    head_name: Optional[str] = None
    account_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
