from __future__ import annotations
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.category import Category
from app.domain.repositories.category_repo import AbstractCategoryRepository
from app.domain.enums.enum import CategoryType
from app.infrastructure.database.models.category import CategoryModel
from app.infrastructure.repositories.mappers import map_category


class SQLAlchemyCategoryRepository(AbstractCategoryRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Category | None:
        result = await self._session.execute(
            select(CategoryModel).where(
                CategoryModel.id == id,
                CategoryModel.is_deleted == False,
            )
        )
        m = result.scalar_one_or_none()
        return map_category(m) if m else None

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 50,
        category_type: CategoryType | None = None,
        include_inactive: bool = False,
    ) -> tuple[list[Category], int]:
        stmt = select(CategoryModel).where(CategoryModel.is_deleted == False)

        if not include_inactive:
            stmt = stmt.where(CategoryModel.is_active == True)
        if category_type:
            stmt = stmt.where(CategoryModel.category_type == category_type)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self._session.scalar(count_stmt)

        stmt = stmt.order_by(CategoryModel.name).offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return [map_category(m) for m in result.scalars().all()], total or 0

    async def get_by_name(self, name: str) -> Category | None:
        result = await self._session.execute(
            select(CategoryModel).where(
                func.lower(CategoryModel.name) == name.strip().lower(),
                CategoryModel.is_deleted == False,
            )
        )
        m = result.scalar_one_or_none()
        return map_category(m) if m else None

    async def exists_by_name(self, name: str) -> bool:
        result = await self._session.execute(
            select(func.count()).select_from(CategoryModel).where(
                func.lower(CategoryModel.name) == name.strip().lower(),
                CategoryModel.is_deleted == False,
            )
        )
        return result.scalar_one() > 0

    async def get_system_categories(self) -> list[Category]:
        result = await self._session.execute(
            select(CategoryModel).where(
                CategoryModel.is_system == True,
                CategoryModel.is_deleted == False,
            )
        )
        return [map_category(m) for m in result.scalars().all()]

    async def get_by_ids(self, ids: list[uuid.UUID]) -> list[Category]:
        result = await self._session.execute(
            select(CategoryModel).where(
                CategoryModel.id.in_(ids),
                CategoryModel.is_deleted == False,
            )
        )
        return [map_category(m) for m in result.scalars().all()]

    async def add(self, category: Category) -> Category:
        m = CategoryModel(
            id=category.id,
            name=category.name,
            category_type=category.category_type,
            description=category.description,
            is_system=category.is_system,
            is_active=category.is_active,
            created_by=category.created_by,
        )
        self._session.add(m)
        await self._session.flush()
        return category

    async def update(self, category: Category) -> Category:
        result = await self._session.execute(
            select(CategoryModel).where(CategoryModel.id == category.id)
        )
        m = result.scalar_one()
        m.name = category.name
        m.description = category.description
        m.is_active = category.is_active
        m.is_deleted = category.is_deleted
        m.deleted_at = category.deleted_at
        m.deleted_by = category.deleted_by
        await self._session.flush()
        return category

    async def delete(self, category: Category) -> None:
        result = await self._session.execute(
            select(CategoryModel).where(CategoryModel.id == category.id)
        )
        m = result.scalar_one()
        await self._session.delete(m)
        await self._session.flush()