from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
import uuid

from pydantic import BaseModel, field_validator

from app.domain.enums.enum import RecordType


class RecordCreate(BaseModel):
    amount: Decimal
    record_type: RecordType
    category_id: uuid.UUID
    record_date: date
    notes: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v


class RecordUpdate(BaseModel):
    amount: Decimal | None = None
    record_type: RecordType | None = None
    category_id: uuid.UUID | None = None
    record_date: date | None = None
    notes: str | None = None


class RecordFilter(BaseModel):
    user_id: uuid.UUID | None = None
    record_type: RecordType | None = None
    category_id: uuid.UUID | None = None
    date_from: date | None = None
    date_to: date | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    search: str | None = None
    page: int = 1
    page_size: int = 20


class RecordResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    amount: Decimal
    record_type: str
    category_id: uuid.UUID
    category_name: str | None
    record_date: date
    notes: str | None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
