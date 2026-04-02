from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from app.domain.entities.permission import Permission


@dataclass
class Role:
    """
    Role domain entity.
    Groups permissions together and is assigned to users.
    Supports dynamic permission assignment at runtime.
    """

    id: uuid.UUID
    name: str
    description: str = ""
    is_active: bool = True
    is_deleted: bool = False
    deleted_at: datetime | None = None
    deleted_by: uuid.UUID | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    permissions: list[Permission] = field(default_factory=list)

    # ── factories ──────────────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        name: str,
        description: str = "",
    ) -> Role:
        return cls(
            id=uuid.uuid4(),
            name=name.strip().lower(),
            description=description,
        )

    # ── behaviour ──────────────────────────────────────────────────────────

    def has_permission(self, permission: str) -> bool:
        """Check if this role grants a specific permission string."""
        if not self.is_active or self.is_deleted:
            return False
        return any(p.codename == permission for p in self.permissions)

    def get_permission_strings(self) -> set[str]:
        """Return all permission codenames this role grants."""
        return {p.codename for p in self.permissions}

    def assign_permission(self, permission: Permission) -> None:
        if not any(p.id == permission.id for p in self.permissions):
            self.permissions.append(permission)

    def remove_permission(self, permission_id: uuid.UUID) -> None:
        self.permissions = [
            p for p in self.permissions if p.id != permission_id
        ]

    def soft_delete(self, deleted_by: uuid.UUID) -> None:
        if self.is_deleted:
            raise ValueError("Role is already deleted")
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False

    # ── representation ─────────────────────────────────────────────────────

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Role):
            return NotImplemented
        return self.id == other.id