from __future__ import annotations
import json
from decimal import Decimal

from app.domain.entities.user import User
from app.domain.repositories.uow import AbstractUnitOfWork
from app.core.cache_service import AbstractCacheService
from app.application.use_cases.dashboard.dtos import TrendsFilterDTO, TrendPointDTO


class GetTrendsUseCase:
    """
    Return time-series income/expense breakdown.

    - Supports "monthly" and "weekly" periods via query param
    - Uses PostgreSQL date_trunc — single aggregation query
    - Cached per user + period combination
    - Returns up to `limit` periods ordered descending
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
        dto: TrendsFilterDTO,
        actor: User,
    ) -> list[TrendPointDTO]:
        if dto.period not in ("monthly", "weekly"):
            raise ValueError("Period must be 'monthly' or 'weekly'")

        user_id = dto.user_id
        if not actor.has_permission("records:read"):
            user_id = actor.id

        cache_key = (
            f"dashboard:trends:{str(user_id) if user_id else 'global'}"
            f":{dto.period}:{dto.limit}"
        )

        # 1. try cache
        cached = await self._get_cache(cache_key)
        if cached is not None:
            return cached

        # 2. DB — single date_trunc + GROUP BY query
        async with self._uow as uow:
            trends = await uow.records.get_trends(
                period=dto.period,
                user_id=user_id,
                limit=dto.limit,
            )

        result = [
            TrendPointDTO(
                period=t.period,
                record_type=t.record_type.value,
                total=t.total,
                count=t.count,
            )
            for t in trends
        ]

        # 3. cache
        await self._set_cache(cache_key, result)
        return result

    async def _get_cache(self, key: str) -> list[TrendPointDTO] | None:
        raw = await self._cache.get(key)
        if raw:
            items = json.loads(raw)
            return [
                TrendPointDTO(**{**item, "total": Decimal(item["total"])})
                for item in items
            ]
        return None

    async def _set_cache(self, key: str, result: list[TrendPointDTO]) -> None:
        data = [
            {
                "period": r.period,
                "record_type": r.record_type,
                "total": str(r.total),
                "count": r.count,
            }
            for r in result
        ]
        await self._cache.set(key, json.dumps(data), self.CACHE_TTL)