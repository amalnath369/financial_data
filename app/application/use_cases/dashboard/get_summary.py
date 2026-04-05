from __future__ import annotations
import json

from app.domain.entities.user import User
from app.domain.repositories.uow import AbstractUnitOfWork
from app.core.cache_service import AbstractCacheService
from app.application.use_cases.dashboard.dtos import DashboardFilterDTO, SummaryResponseDTO


class GetDashboardSummaryUseCase:
    """
    Return total income, expense, net balance, and record count.

    Strategy:
    1. Check Redis cache (TTL 5 min)
    2. On miss → single PostgreSQL aggregation query (no Python summing)
    3. Store result in Redis
    4. On Redis failure → degrade gracefully, always hit DB
    """

    CACHE_TTL = 300  # 5 minutes

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
    ) -> SummaryResponseDTO:
        # viewers are always scoped to their own data
        user_id = dto.user_id
        if not actor.has_permission("records:read"):
            user_id = actor.id

        cache_key = self._cache_key(user_id, dto)

        # 1. try cache
        cached = await self._get_cache(cache_key)
        if cached:
            return SummaryResponseDTO(**cached, cached=True)

        # 2. DB aggregation — single query, no Python summing
        async with self._uow as uow:
            summary = await uow.records.get_dashboard_summary(
                user_id=user_id,
                date_from=dto.date_from,
                date_to=dto.date_to,
            )

        result = SummaryResponseDTO(
            total_income=summary.total_income,
            total_expense=summary.total_expense,
            net_balance=summary.net_balance,
            total_records=summary.total_records,
            cached=False,
        )

        # 3. store in cache
        await self._set_cache(cache_key, result)
        return result

    def _cache_key(self, user_id, dto: DashboardFilterDTO) -> str:
        uid = str(user_id) if user_id else "global"
        date_from = dto.date_from.isoformat() if dto.date_from else "all"
        date_to = dto.date_to.isoformat() if dto.date_to else "all"
        return f"dashboard:summary:{uid}:{date_from}:{date_to}"

    async def _get_cache(self, key: str) -> dict | None:
        raw = await self._cache.get(key)
        if raw:
            from decimal import Decimal
            data = json.loads(raw)
            for field in ("total_income", "total_expense", "net_balance"):
                data[field] = Decimal(data[field])
            return data
        return None

    async def _set_cache(self, key: str, result: SummaryResponseDTO) -> None:
        data = {
            "total_income": str(result.total_income),
            "total_expense": str(result.total_expense),
            "net_balance": str(result.net_balance),
            "total_records": result.total_records,
        }
        await self._cache.set(key, json.dumps(data), self.CACHE_TTL)