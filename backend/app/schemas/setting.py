from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SettingBase(BaseModel):
    key: str = Field(..., max_length=100)
    value: Optional[str] = None
    is_active: bool = True


class SettingCreate(SettingBase):
    pass


class SettingUpdate(BaseModel):
    value: Optional[str] = None
    is_active: Optional[bool] = None


class SettingRead(SettingBase):
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
