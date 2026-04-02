from __future__ import annotations
import uuid

from app.domain.entities.category import Category
from app.domain.repositories.uow import AbstractUnitOfWork
from app.application.use_cases.categories.dtos import GetCategoriesDTO


class GetCategoriesUseCase:
    """
    Paginated list of categories.
    Optionally filtered by type.
    All roles can access this.
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self, dto: GetCategoriesDTO
    ) -> tuple[list[Category], int]:
        async with self._uow as uow:
            return await uow.categories.get_all(
                page=dto.page,
                page_size=dto.page_size,
                category_type=dto.category_type,
                include_inactive=dto.include_inactive,
            )


class GetCategoryUseCase:
    """Fetch a single category by ID."""

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, category_id: uuid.UUID) -> Category:
        async with self._uow as uow:
            category = await uow.categories.get_by_id(category_id)
            if not category or category.is_deleted:
                raise ValueError(f"Category {category_id} not found")
            return category