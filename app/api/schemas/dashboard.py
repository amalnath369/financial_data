from __future__ import annotations
from decimal import Decimal

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    net_balance: Decimal
    total_records: int
    cached: bool


class CategoryTotalResponse(BaseModel):
    category_id: str
    category_name: str
    record_type: str
    total: Decimal
    count: int


class TrendPointResponse(BaseModel):
    period: str
    record_type: str
    total: Decimal
    count: int
