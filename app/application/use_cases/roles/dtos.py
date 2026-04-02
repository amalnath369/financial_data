from __future__ import annotations
from dataclasses import dataclass, field
import uuid


@dataclass
class CreateRoleDTO:
    name: str
    description: str = ""
    permission_ids: list[uuid.UUID] = field(default_factory=list)


@dataclass
class UpdateRoleDTO:
    role_id: uuid.UUID
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


@dataclass
class AssignPermissionsDTO:
    role_id: uuid.UUID
    permission_ids: list[uuid.UUID]


@dataclass
class RemovePermissionsDTO:
    role_id: uuid.UUID
    permission_ids: list[uuid.UUID]


@dataclass
class GetRolesDTO:
    include_inactive: bool = False
    page: int = 1
    page_size: int = 50