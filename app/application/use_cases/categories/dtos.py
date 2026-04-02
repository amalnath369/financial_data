from __future__ import annotations
from dataclasses import dataclass
import uuid

from app.domain.enums.enum import CategoryType


@dataclass
class CreateCategoryDTO:
    name: str
    category_type: CategoryType
    description: str = ""


@dataclass
class UpdateCategoryDTO:
    category_id: uuid.UUID
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


@dataclass
class GetCategoriesDTO:
    category_type: CategoryType | None = None
    include_inactive: bool = False
    page: int = 1
    page_size: int = 50