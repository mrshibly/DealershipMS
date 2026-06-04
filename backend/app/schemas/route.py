"""
Pydantic schemas for Route endpoints.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel


class RouteCreate(BaseModel):
    name: str
    area: str | None = None
    description: str | None = None


class RouteRead(BaseModel):
    id: uuid.UUID
    name: str
    area: str | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RouteUpdate(BaseModel):
    name: str | None = None
    area: str | None = None
    description: str | None = None
    is_active: bool | None = None
