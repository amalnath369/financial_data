from __future__ import annotations
from datetime import datetime
import uuid

from pydantic import BaseModel


class PermissionResponse(BaseModel):
    id: uuid.UUID
    codename: str
    resource: str
    action: str
    description: str


class RoleCreate(BaseModel):
    name: str
    description: str = ""
    permission_ids: list[uuid.UUID] = []


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class AssignPermissionsRequest(BaseModel):
    permission_ids: list[uuid.UUID]


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    is_active: bool
    permissions: list[PermissionResponse] = []
    created_at: datetime
    updated_at: datetime
