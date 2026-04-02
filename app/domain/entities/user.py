from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from app.domain.value_objects.email import Email
from app.domain.value_objects.password import Password
from app.domain.enums.enum import UserStatus
from app.domain.entities.role import Role


@dataclass
class User:
    """
    User domain entity.
    - Uses Email + Password value objects
    - Tracks status, soft delete, and assigned roles
    - No framework dependencies
    """

    id: uuid.UUID
    email: Email
    password: Password
    full_name: str
    status: UserStatus = UserStatus.ACTIVE
    is_deleted: bool = False
    deleted_at: datetime | None = None
    deleted_by: uuid.UUID | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    roles: list[Role] = field(default_factory=list)

    # ── factories ──────────────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        email: str,
        password: str,
        full_name: str,
    ) -> User:
        """
        Factory for creating a brand-new user.
        Validates email + password via value objects.
        """
        return cls(
            id=uuid.uuid4(),
            email=Email(email),
            password=Password(password),
            full_name=full_name.strip(),
            status=UserStatus.ACTIVE,
        )

    # ── behaviour ──────────────────────────────────────────────────────────

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE and not self.is_deleted

    def activate(self) -> None:
        if self.is_deleted:
            raise ValueError("Cannot activate a deleted user")
        self.status = UserStatus.ACTIVE

    def deactivate(self) -> None:
        self.status = UserStatus.INACTIVE

    def soft_delete(self, deleted_by: uuid.UUID) -> None:
        if self.is_deleted:
            raise ValueError("User is already deleted")
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by

    def change_password(self, new_password: str) -> None:
        self.password = Password(new_password)

    def update_profile(self, full_name: str | None = None) -> None:
        if full_name is not None:
            self.full_name = full_name.strip()

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission through any of their roles."""
        return any(role.has_permission(permission) for role in self.roles)

    def get_all_permissions(self) -> set[str]:
        """Collect all unique permissions across all assigned roles."""
        permissions: set[str] = set()
        for role in self.roles:
            permissions.update(role.get_permission_strings())
        return permissions

    def assign_role(self, role: Role) -> None:
        if not any(r.id == role.id for r in self.roles):
            self.roles.append(role)

    def remove_role(self, role_id: uuid.UUID) -> None:
        self.roles = [r for r in self.roles if r.id != role_id]

    def get_role_names(self) -> list[str]:
        return [r.name for r in self.roles]

    # ── representation ─────────────────────────────────────────────────────

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id