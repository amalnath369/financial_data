from __future__ import annotations
from abc import abstractmethod
import uuid

from app.domain.repositories.base import AbstractBaseRepository
from app.domain.entities.category import Category
from app.domain.enums.enum import CategoryType


class AbstractCategoryRepository(AbstractBaseRepository[Category]):
    """
    Category-specific repository interface.
    """

    @abstractmethod
    async def get_all(
        self,
        page: int = 1,
        page_size: int = 50,
        category_type: CategoryType | None = None,
        include_inactive: bool = False,
    ) -> tuple[list[Category], int]:
        """
        Paginated list of categories.
        Optionally filter by type.
        Returns (categories, total_count).
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_name(self, name: str) -> Category | None:
        """Fetch a category by exact name (case-insensitive)."""
        raise NotImplementedError

    @abstractmethod
    async def exists_by_name(self, name: str) -> bool:
        """Check for name uniqueness before create/update."""
        raise NotImplementedError

    @abstractmethod
    async def get_system_categories(self) -> list[Category]:
        """Return all seeded system categories."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_ids(self, ids: list[uuid.UUID]) -> list[Category]:
        """Batch fetch categories by a list of IDs. Avoids N+1 in dashboards."""
        raise NotImplementedError