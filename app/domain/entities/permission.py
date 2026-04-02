from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Permission:
    """
    Permission domain entity.
    Represents a single action on a resource — e.g. records:create
    Seeded at startup and never changed at runtime.
    """

    id: uuid.UUID
    resource: str
    action: str
    description: str = ""
    is_deleted: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # ── factories ──────────────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        resource: str,
        action: str,
        description: str = "",
    ) -> Permission:
        return cls(
            id=uuid.uuid4(),
            resource=resource,
            action=action,
            description=description,
        )

    # ── behaviour ──────────────────────────────────────────────────────────

    @property
    def codename(self) -> str:
        """Returns the permission string e.g. records:create"""
        return f"{self.resource}:{self.action}"

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Permission):
            return NotImplemented
        return self.id == other.id