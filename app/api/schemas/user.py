from __future__ import annotations
from datetime import datetime
import uuid

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role_names: list[str] = ["viewer"]


class UserUpdate(BaseModel):
    full_name: str | None = None


class ChangeStatusRequest(BaseModel):
    is_active: bool


class AssignRoleRequest(BaseModel):
    role_id: uuid.UUID


class PermissionResponse(BaseModel):
    id: uuid.UUID
    codename: str
    resource: str
    action: str
    description: str


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    is_active: bool
    permissions: list[PermissionResponse] = []


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    status: str
    is_deleted: bool
    roles: list[RoleResponse] = []
    created_at: datetime
    updated_at: datetime
