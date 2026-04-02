from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from app.domain.enums.enum import CategoryType


@dataclass
class Category:
    """
    Category domain entity.
    - is_system = True means seeded, protected from deletion/update
    - category_type indicates whether it applies to income, expense, or both
    """

    id: uuid.UUID
    name: str
    category_type: CategoryType
    description: str = ""
    is_system: bool = False
    is_active: bool = True
    is_deleted: bool = False
    deleted_at: datetime | None = None
    deleted_by: uuid.UUID | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # ── factories ──────────────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        name: str,
        category_type: CategoryType,
        description: str = "",
        created_by: uuid.UUID | None = None,
        is_system: bool = False,
    ) -> Category:
        return cls(
            id=uuid.uuid4(),
            name=name.strip(),
            category_type=category_type,
            description=description,
            created_by=created_by,
            is_system=is_system,
        )

    # ── behaviour ──────────────────────────────────────────────────────────

    def update(
        self,
        name: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> None:
        if self.is_system:
            raise ValueError(
                f"System category {self.name!r} cannot be modified"
            )
        if name is not None:
            self.name = name.strip()
        if description is not None:
            self.description = description
        if is_active is not None:
            self.is_active = is_active
        self.updated_at = datetime.utcnow()

    def soft_delete(self, deleted_by: uuid.UUID) -> None:
        if self.is_system:
            raise ValueError(
                f"System category {self.name!r} cannot be deleted"
            )
        if self.is_deleted:
            raise ValueError("Category is already deleted")
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by

    # ── representation ─────────────────────────────────────────────────────

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Category):
            return NotImplemented
        return self.id == other.id