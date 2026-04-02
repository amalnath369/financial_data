from __future__ import annotations
from dataclasses import dataclass
import uuid


@dataclass
class CreateUserDTO:
    email: str
    password: str
    full_name: str
    role_names: list[str]


@dataclass
class UpdateUserDTO:
    user_id: uuid.UUID
    full_name: str | None = None


@dataclass
class ChangeStatusDTO:
    user_id: uuid.UUID
    is_active: bool


@dataclass
class AssignRoleDTO:
    user_id: uuid.UUID
    role_id: uuid.UUID


@dataclass
class RemoveRoleDTO:
    user_id: uuid.UUID
    role_id: uuid.UUID


@dataclass
class GetUsersDTO:
    page: int = 1
    page_size: int = 20
    search: str | None = None
    include_deleted: bool = False