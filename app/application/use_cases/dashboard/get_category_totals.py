from __future__ import annotations
import json
from decimal import Decimal

from app.domain.entities.user import User
from app.domain.repositories.uow import AbstractUnitOfWork
from app.core.cache_service import AbstractCacheService
from app.application.use_cases.dashboard.dtos import DashboardFilterDTO, CategoryTotalDTO


class GetCategoryTotalsUseCase:
    """
    Return per-category breakdown of income and expense totals.

    - Single GROUP BY query in PostgreSQL — no N+1, no Python aggregation
    - Cached in Redis for 5 minutes per user/filter combination
    - Degrades gracefully if Redis is unavailable
    """

    CACHE_TTL = 300

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        cache: AbstractCacheService,
    ) -> None:
        self._uow = uow
        self._cache = cache

    async def execute(
        self,
        dto: DashboardFilterDTO,
        actor: User,
    ) -> list[CategoryTotalDTO]:
        user_id = dto.user_id
        if not actor.has_permission("records:read"):
            user_id = actor.id

        cache_key = self._cache_key(user_id, dto)

        # 1. try cache
        cached = await self._get_cache(cache_key)
        if cached is not None:
            return cached

        # 2. DB — single GROUP BY query
        async with self._uow as uow:
            totals = await uow.records.get_category_totals(
                user_id=user_id,
                date_from=dto.date_from,
                date_to=dto.date_to,
            )

        result = [
            CategoryTotalDTO(
                category_id=str(t.category_id),
                category_name=t.category_name,
                record_type=t.record_type.value,
                total=t.total,
                count=t.count,
            )
            for t in totals
        ]

        # 3. cache
        await self._set_cache(cache_key, result)
        return result

    def _cache_key(self, user_id, dto: DashboardFilterDTO) -> str:
        uid = str(user_id) if user_id else "global"
        date_from = dto.date_from.isoformat() if dto.date_from else "all"
        date_to = dto.date_to.isoformat() if dto.date_to else "all"
        return f"dashboard:categories:{uid}:{date_from}:{date_to}"

    async def _get_cache(self, key: str) -> list[CategoryTotalDTO] | None:
        raw = await self._cache.get(key)
        if raw:
            items = json.loads(raw)
            return [
                CategoryTotalDTO(**{**item, "total": Decimal(item["total"])})
                for item in items
            ]
        return None

    async def _set_cache(self, key: str, result: list[CategoryTotalDTO]) -> None:
        data = [
            {
                "category_id": r.category_id,
                "category_name": r.category_name,
                "record_type": r.record_type,
                "total": str(r.total),
                "count": r.count,
            }
            for r in result
        ]
        await self._cache.set(key, json.dumps(data), self.CACHE_TTL)