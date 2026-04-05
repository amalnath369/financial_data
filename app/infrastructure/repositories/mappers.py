from __future__ import annotations

from app.domain.entities.user import User
from app.domain.entities.role import Role
from app.domain.entities.permission import Permission
from app.domain.entities.category import Category
from app.domain.entities.record import FinancialRecord
from app.domain.entities.audit import AuditLog
from app.domain.value_objects.email import Email
from app.domain.value_objects.money import Money
from app.domain.value_objects.password import Password

from app.infrastructure.database.models.users import UserModel
from app.infrastructure.database.models.roles import RoleModel
from app.infrastructure.database.models.permission import PermissionModel
from app.infrastructure.database.models.category import CategoryModel
from app.infrastructure.database.models.record import FinancialRecordModel
from app.infrastructure.database.models.audit import AuditLogModel


def map_permission(m: PermissionModel) -> Permission:
    return Permission(
        id=m.id,
        resource=m.resource,
        action=m.action,
        description=m.description,
        is_deleted=m.is_deleted,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def map_role(m: RoleModel) -> Role:
    permissions = [
        map_permission(rp.permission)
        for rp in (m.role_permissions or [])
        if rp.permission and not rp.permission.is_deleted
    ]
    return Role(
        id=m.id,
        name=m.name,
        description=m.description,
        is_active=m.is_active,
        is_deleted=m.is_deleted,
        deleted_at=m.deleted_at,
        deleted_by=m.deleted_by,
        created_at=m.created_at,
        updated_at=m.updated_at,
        permissions=permissions,
    )


def map_user(m: UserModel) -> User:
    roles = [
        map_role(ur.role)
        for ur in (m.user_roles or [])
        if ur.role and not ur.role.is_deleted
    ]
    return User(
        id=m.id,
        email=Email(m.email),
        password=Password.from_hash(m.hashed_password),
        full_name=m.full_name,
        status=m.status,
        is_deleted=m.is_deleted,
        deleted_at=m.deleted_at,
        deleted_by=m.deleted_by,
        created_at=m.created_at,
        updated_at=m.updated_at,
        roles=roles,
    )


def map_category(m: CategoryModel) -> Category:
    return Category(
        id=m.id,
        name=m.name,
        category_type=m.category_type,
        description=m.description,
        is_system=m.is_system,
        is_active=m.is_active,
        is_deleted=m.is_deleted,
        deleted_at=m.deleted_at,
        deleted_by=m.deleted_by,
        created_by=m.created_by,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def map_record(m: FinancialRecordModel) -> FinancialRecord:
    return FinancialRecord(
        id=m.id,
        user_id=m.user_id,
        amount=Money(m.amount),
        record_type=m.record_type,
        category_id=m.category_id,
        record_date=m.record_date,
        notes=m.notes,
        is_deleted=m.is_deleted,
        deleted_at=m.deleted_at,
        deleted_by=m.deleted_by,
        created_at=m.created_at,
        updated_at=m.updated_at,
        category_name=m.category.name if m.category else None,
    )


def map_audit(m: AuditLogModel) -> AuditLog:
    return AuditLog(
        id=m.id,
        actor_id=m.actor_id,
        actor_email=m.actor_email,
        actor_roles=m.actor_roles,
        action=m.action,
        resource=m.resource,
        resource_id=m.resource_id,
        before=m.before,
        after=m.after,
        diff=m.diff,
        request_id=m.request_id,
        ip_address=m.ip_address,
        user_agent=m.user_agent,
        status=m.status,
        failure_reason=m.failure_reason,
        timestamp=m.timestamp,
    )