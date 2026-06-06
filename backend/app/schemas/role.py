import uuid
from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    name: str = Field(..., max_length=100)
    permissions: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    permissions: Dict[str, Any] | None = None
    is_active: bool | None = None


class RoleRead(RoleBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
