from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import uuid

from app.domain.enums.enum import RecordType


@dataclass
class DashboardFilterDTO:
    user_id: uuid.UUID | None = None   # None = all users (admin view)
    date_from: date | None = None
    date_to: date | None = None


@dataclass
class TrendsFilterDTO:
    period: str = "monthly"            # "monthly" | "weekly"
    user_id: uuid.UUID | None = None
    limit: int = 12


@dataclass
class SummaryResponseDTO:
    total_income: Decimal
    total_expense: Decimal
    net_balance: Decimal
    total_records: int
    cached: bool = False


@dataclass
class CategoryTotalDTO:
    category_id: str
    category_name: str
    record_type: str
    total: Decimal
    count: int


@dataclass
class TrendPointDTO:
    period: str
    record_type: str
    total: Decimal
    count: int