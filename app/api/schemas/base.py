from __future__ import annotations
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: list[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        pages = max(1, -(-total // page_size))  # ceiling division
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class SuccessResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
