from __future__ import annotations
from datetime import datetime
import uuid

from pydantic import BaseModel

from app.domain.enums.enum import CategoryType


class CategoryCreate(BaseModel):
    name: str
    category_type: CategoryType
    description: str = ""


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class CategoryFilter(BaseModel):
    category_type: CategoryType | None = None
    include_inactive: bool = False
    page: int = 1
    page_size: int = 50


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    category_type: str
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
