from __future__ import annotations
from abc import abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import uuid

from app.domain.repositories.base import AbstractBaseRepository
from app.domain.entities.record import FinancialRecord
from app.domain.enums.enum import RecordType


@dataclass
class RecordFilters:
    """
    All supported filter params for record listing.
    Each field is optional — only applied when provided.
    """
    user_id: uuid.UUID | None = None          # scope to specific user
    record_type: RecordType | None = None     # income / expense
    category_id: uuid.UUID | None = None      # specific category
    date_from: date | None = None             # range start
    date_to: date | None = None               # range end
    min_amount: Decimal | None = None         # amount floor
    max_amount: Decimal | None = None         # amount ceiling
    search: str | None = None                 # full-text search
    page: int = 1
    page_size: int = 20


@dataclass
class DashboardSummary:
    """Aggregated financial summary returned by dashboard use case."""
    total_income: Decimal
    total_expense: Decimal
    net_balance: Decimal
    total_records: int


@dataclass
class CategoryTotal:
    """Per-category aggregation for dashboard breakdown."""
    category_id: uuid.UUID
    category_name: str
    record_type: RecordType
    total: Decimal
    count: int


@dataclass
class TrendPoint:
    """Single data point in a trend series (monthly or weekly)."""
    period: str           # e.g. "2026-03" for monthly, "2026-W12" for weekly
    record_type: RecordType
    total: Decimal
    count: int


class AbstractRecordRepository(AbstractBaseRepository[FinancialRecord]):
    """
    Financial record-specific repository interface.
    Extends base CRUD with filtering, search, and dashboard aggregations.
    """

    @abstractmethod
    async def get_by_id_with_category(
        self, id: uuid.UUID
    ) -> FinancialRecord | None:
        """Fetch a record with category eagerly loaded."""
        raise NotImplementedError

    @abstractmethod
    async def get_all(
        self, filters: RecordFilters
    ) -> tuple[list[FinancialRecord], int]:
        """
        Paginated, filtered, searchable record list.
        Eager loads category.
        Returns (records, total_count).
        """
        raise NotImplementedError

    @abstractmethod
    async def get_dashboard_summary(
        self,
        user_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> DashboardSummary:
        """
        Single aggregation query for total income, expense, net balance.
        No Python-level summing — all done in Postgres.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_category_totals(
        self,
        user_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[CategoryTotal]:
        """
        Category-wise breakdown of totals.
        Single GROUP BY query — no N+1.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_trends(
        self,
        period: str,                          # "monthly" | "weekly"
        user_id: uuid.UUID | None = None,
        limit: int = 12,
    ) -> list[TrendPoint]:
        """
        Time-series aggregation using date_trunc.
        Returns up to `limit` periods descending.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_recent(
        self,
        user_id: uuid.UUID | None = None,
        limit: int = 10,
    ) -> list[FinancialRecord]:
        """Most recent records ordered by record_date desc."""
        raise NotImplementedError