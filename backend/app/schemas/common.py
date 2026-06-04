"""
Standard API response envelope.
All endpoints must use these wrappers.
"""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str = "OK"


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    total: int
    page: int
    per_page: int
    pages: int
    message: str = "OK"
