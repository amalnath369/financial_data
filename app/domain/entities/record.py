from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
import uuid

from app.domain.value_objects.money import Money
from app.domain.enums.enum import RecordType


@dataclass
class FinancialRecord:
    """
    Financial record domain entity.
    - Uses Money value object for amount precision + validation
    - Tracks income or expense via RecordType enum
    - Supports soft delete with who/when
    - update() returns diff dict consumed by audit log
    """

    id: uuid.UUID
    user_id: uuid.UUID
    amount: Money
    record_type: RecordType
    category_id: uuid.UUID
    record_date: date
    notes: str | None = None
    is_deleted: bool = False
    deleted_at: datetime | None = None
    deleted_by: uuid.UUID | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    # eagerly loaded when available — not persisted here
    category_name: str | None = None

    # ── factories ──────────────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        user_id: uuid.UUID,
        amount: Money,
        record_type: RecordType,
        category_id: uuid.UUID,
        record_date: date,
        notes: str | None = None,
    ) -> FinancialRecord:
        return cls(
            id=uuid.uuid4(),
            user_id=user_id,
            amount=amount,
            record_type=record_type,
            category_id=category_id,
            record_date=record_date,
            notes=notes,
        )

    # ── behaviour ──────────────────────────────────────────────────────────

    def update(
        self,
        amount: Money | None = None,
        record_type: RecordType | None = None,
        category_id: uuid.UUID | None = None,
        record_date: date | None = None,
        notes: str | None = None,
    ) -> dict:
        """
        Update allowed fields.
        Returns a diff dict of what changed — consumed by audit logging.
        """
        if self.is_deleted:
            raise ValueError("Cannot update a deleted record")

        before = self._snapshot()

        if amount is not None:
            self.amount = amount
        if record_type is not None:
            self.record_type = record_type
        if category_id is not None:
            self.category_id = category_id
        if record_date is not None:
            self.record_date = record_date
        if notes is not None:
            self.notes = notes

        self.updated_at = datetime.utcnow()
        after = self._snapshot()

        return self._compute_diff(before, after)

    def soft_delete(self, deleted_by: uuid.UUID) -> None:
        if self.is_deleted:
            raise ValueError("Record is already deleted")
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by

    def belongs_to(self, user_id: uuid.UUID) -> bool:
        return self.user_id == user_id

    # ── snapshots for audit ─────────────────────────────────────────────────

    def _snapshot(self) -> dict:
        return {
            "amount": str(self.amount.amount),
            "record_type": self.record_type.value,
            "category_id": str(self.category_id),
            "record_date": self.record_date.isoformat(),
            "notes": self.notes,
        }

    @staticmethod
    def _compute_diff(before: dict, after: dict) -> dict:
        return {
            key: {"from": before[key], "to": after[key]}
            for key in before
            if before[key] != after[key]
        }

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            **self._snapshot(),
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    # ── representation ─────────────────────────────────────────────────────

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FinancialRecord):
            return NotImplemented
        return self.id == other.id