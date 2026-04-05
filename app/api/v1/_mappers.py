"""
Shared entity → schema mappers used across multiple routers.
Kept here to avoid duplication without polluting the schemas layer.
"""
from __future__ import annotations

from app.api.schemas.user import UserResponse, RoleResponse, PermissionResponse
from app.api.schemas.record import RecordResponse
from app.api.schemas.category import CategoryResponse
from app.api.schemas.role import RoleResponse as RoleDetailResponse, PermissionResponse as PermDetailResponse


def map_permission(p) -> PermissionResponse:
    return PermissionResponse(
        id=p.id,
        codename=p.codename,
        resource=p.resource,
        action=p.action,
        description=p.description,
    )


def map_role_summary(r) -> RoleResponse:
    return RoleResponse(
        id=r.id,
        name=r.name,
        description=r.description,
        is_active=r.is_active,
        permissions=[map_permission(p) for p in r.permissions],
    )


def map_user(user) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=str(user.email),
        full_name=user.full_name,
        status=user.status.value,
        is_deleted=user.is_deleted,
        roles=[map_role_summary(r) for r in user.roles],
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def map_record(record) -> RecordResponse:
    return RecordResponse(
        id=record.id,
        user_id=record.user_id,
        amount=record.amount.to_decimal(),
        record_type=record.record_type.value,
        category_id=record.category_id,
        category_name=record.category_name,
        record_date=record.record_date,
        notes=record.notes,
        is_deleted=record.is_deleted,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def map_category(cat) -> CategoryResponse:
    return CategoryResponse(
        id=cat.id,
        name=cat.name,
        description=cat.description,
        category_type=cat.category_type.value,
        is_system=cat.is_system,
        is_active=cat.is_active,
        created_at=cat.created_at,
        updated_at=cat.updated_at,
    )


def map_role_detail(r) -> RoleDetailResponse:
    return RoleDetailResponse(
        id=r.id,
        name=r.name,
        description=r.description,
        is_active=r.is_active,
        permissions=[
            PermDetailResponse(
                id=p.id,
                codename=p.codename,
                resource=p.resource,
                action=p.action,
                description=p.description,
            )
            for p in r.permissions
        ],
        created_at=r.created_at,
        updated_at=r.updated_at,
    )
