import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TargetBase(BaseModel):
    dsr_id: uuid.UUID
    target_month: date
    target_amount: float = Field(0.0, ge=0.0)


class TargetCreate(TargetBase):
    pass


class TargetUpdate(BaseModel):
    target_amount: float | None = Field(None, ge=0.0)


class TargetRead(TargetBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    dsr_name: str | None = None
    achieved_amount: float = 0.0

    model_config = ConfigDict(from_attributes=True)
