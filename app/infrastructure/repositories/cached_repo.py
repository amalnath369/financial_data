from __future__ import annotations
import json
from datetime import date
from decimal import Decimal
from typing import Any
import uuid

from app.domain.entities.record import FinancialRecord
from app.domain.repositories.record_repo import (
    AbstractRecordRepository,
    RecordFilters,
    DashboardSummary,
    CategoryTotal,
    TrendPoint,
)
from app.domain.enums.enum import RecordType
from app.core.cache_service import AbstractCacheService


class CachedRecordRepository(AbstractRecordRepository):
    """
    Decorator pattern.

    Implements AbstractRecordRepository — same interface as SQLAlchemyRecordRepository.
    Wraps the real SQLAlchemyRecordRepository which is also AbstractRecordRepository.

    UoW creates:
        raw  = SQLAlchemyRecordRepository(session)   ← AbstractRecordRepository
        self.records = CachedRecordRepository(raw, redis)  ← AbstractRecordRepository

    Use cases only ever see AbstractRecordRepository — completely unaware of caching.

    Cached reads (5 min TTL):
        get_dashboard_summary  → Redis → DB on miss
        get_category_totals    → Redis → DB on miss
        get_trends             → Redis → DB on miss

    Write-through invalidation:
        add / update / delete  → DB write → invalidate Redis keys

    Everything else passes straight through to the wrapped repo.
    Redis failure ALWAYS degrades gracefully — never crashes.
    """

    CACHE_TTL = 300  # 5 minutes

    def __init__(
        self,
        repo: AbstractRecordRepository,
        cache: AbstractCacheService,
    ) -> None:
        self._repo = repo
        self._cache = cache

    # ── passthrough — no caching needed ───────────────────────────────────

    async def get_by_id(self, id: uuid.UUID) -> FinancialRecord | None:
        return await self._repo.get_by_id(id)

    async def get_by_id_with_category(self, id: uuid.UUID) -> FinancialRecord | None:
        return await self._repo.get_by_id_with_category(id)

    async def get_all(
        self, filters: RecordFilters
    ) -> tuple[list[FinancialRecord], int]:
        # not cached — filter combinations too varied, must always be fresh
        return await self._repo.get_all(filters)

    async def get_recent(
        self,
        user_id: uuid.UUID | None = None,
        limit: int = 10,
    ) -> list[FinancialRecord]:
        # not cached — always real-time
        return await self._repo.get_recent(user_id=user_id, limit=limit)

    # ── cached reads ───────────────────────────────────────────────────────

    async def get_dashboard_summary(
        self,
        user_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> DashboardSummary:
        key = self._summary_key(user_id, date_from, date_to)

        cached = await self._cache_get(key)
        if cached:
            return DashboardSummary(
                total_income=Decimal(cached["total_income"]),
                total_expense=Decimal(cached["total_expense"]),
                net_balance=Decimal(cached["net_balance"]),
                total_records=cached["total_records"],
            )

        summary = await self._repo.get_dashboard_summary(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
        )

        await self._cache_set(key, {
            "total_income": str(summary.total_income),
            "total_expense": str(summary.total_expense),
            "net_balance": str(summary.net_balance),
            "total_records": summary.total_records,
        })

        return summary

    async def get_category_totals(
        self,
        user_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[CategoryTotal]:
        key = self._category_key(user_id, date_from, date_to)

        cached = await self._cache_get(key)
        if cached:
            return [
                CategoryTotal(
                    category_id=uuid.UUID(item["category_id"]),
                    category_name=item["category_name"],
                    record_type=RecordType(item["record_type"]),
                    total=Decimal(item["total"]),
                    count=item["count"],
                )
                for item in cached
            ]

        totals = await self._repo.get_category_totals(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
        )

        await self._cache_set(key, [
            {
                "category_id": str(t.category_id),
                "category_name": t.category_name,
                "record_type": t.record_type.value,
                "total": str(t.total),
                "count": t.count,
            }
            for t in totals
        ])

        return totals

    async def get_trends(
        self,
        period: str,
        user_id: uuid.UUID | None = None,
        limit: int = 12,
    ) -> list[TrendPoint]:
        key = self._trends_key(user_id, period, limit)

        cached = await self._cache_get(key)
        if cached:
            return [
                TrendPoint(
                    period=item["period"],
                    record_type=RecordType(item["record_type"]),
                    total=Decimal(item["total"]),
                    count=item["count"],
                )
                for item in cached
            ]

        trends = await self._repo.get_trends(
            period=period,
            user_id=user_id,
            limit=limit,
        )

        await self._cache_set(key, [
            {
                "period": t.period,
                "record_type": t.record_type.value,
                "total": str(t.total),
                "count": t.count,
            }
            for t in trends
        ])

        return trends

    # ── writes — DB first, then invalidate cache ───────────────────────────

    async def add(self, record: FinancialRecord) -> FinancialRecord:
        result = await self._repo.add(record)
        await self._invalidate(record.user_id)
        return result

    async def update(self, record: FinancialRecord) -> FinancialRecord:
        result = await self._repo.update(record)
        await self._invalidate(record.user_id)
        return result

    async def delete(self, record: FinancialRecord) -> None:
        await self._repo.delete(record)
        await self._invalidate(record.user_id)

    # ── cache internals ────────────────────────────────────────────────────

    async def _cache_get(self, key: str) -> Any | None:
        raw = await self._cache.get(key)
        if raw:
            return json.loads(raw)
        return None

    async def _cache_set(self, key: str, value: Any) -> None:
        await self._cache.set(key, json.dumps(value), self.CACHE_TTL)

    async def _invalidate(self, user_id: uuid.UUID) -> None:
        uid = str(user_id)
        user_keys = await self._cache.keys(f"dashboard:*:{uid}:*")
        global_keys = await self._cache.keys("dashboard:*:global:*")
        all_keys = user_keys + global_keys
        if all_keys:
            await self._cache.delete(*all_keys)

    # ── cache key builders ─────────────────────────────────────────────────

    @staticmethod
    def _summary_key(
        user_id: uuid.UUID | None,
        date_from: date | None,
        date_to: date | None,
    ) -> str:
        uid = str(user_id) if user_id else "global"
        df = date_from.isoformat() if date_from else "all"
        dt = date_to.isoformat() if date_to else "all"
        return f"dashboard:summary:{uid}:{df}:{dt}"

    @staticmethod
    def _category_key(
        user_id: uuid.UUID | None,
        date_from: date | None,
        date_to: date | None,
    ) -> str:
        uid = str(user_id) if user_id else "global"
        df = date_from.isoformat() if date_from else "all"
        dt = date_to.isoformat() if date_to else "all"
        return f"dashboard:categories:{uid}:{df}:{dt}"

    @staticmethod
    def _trends_key(
        user_id: uuid.UUID | None,
        period: str,
        limit: int,
    ) -> str:
        uid = str(user_id) if user_id else "global"
        return f"dashboard:trends:{uid}:{period}:{limit}"