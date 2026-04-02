from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
import uuid

from app.domain.enums.enum import RecordType


@dataclass
class CreateRecordDTO:
    amount: Decimal
    record_type: RecordType
    category_id: uuid.UUID
    record_date: date
    notes: str | None = None


@dataclass
class UpdateRecordDTO:
    record_id: uuid.UUID
    amount: Decimal | None = None
    record_type: RecordType | None = None
    category_id: uuid.UUID | None = None
    record_date: date | None = None
    notes: str | None = None


@dataclass
class GetRecordsDTO:
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