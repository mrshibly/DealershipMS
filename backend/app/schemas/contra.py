import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

class ContraEntryBase(BaseModel):
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount: float = Field(..., gt=0)
    date: date
    narration: Optional[str] = None
    reference: Optional[str] = Field(None, max_length=100)

class ContraEntryCreate(ContraEntryBase):
    pass

class ContraEntryRead(ContraEntryBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    # Enrichment
    from_account_name: Optional[str] = None
    to_account_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
