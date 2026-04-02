from __future__ import annotations

from app.domain.entities.user import User
from app.domain.entities.role import Role
from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.enums.action_type import ActionType
from app.application.use_cases.roles.dtos import AssignPermissionsDTO, RemovePermissionsDTO


class AssignPermissionsToRoleUseCase:
    """
    Assign one or more permissions to a role.
    - All permission IDs must exist
    - Idempotent — already-assigned permissions are skipped
    - Logs before/after permission snapshot in audit
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        dto: AssignPermissionsDTO,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> Role:
        async with self._uow as uow:
            role = await uow.roles.get_by_id_with_permissions(dto.role_id)
            if not role or role.is_deleted:
                raise ValueError(f"Role {dto.role_id} not found")

            permissions = await uow.permissions.get_by_ids(dto.permission_ids)
            if len(permissions) != len(dto.permission_ids):
                raise ValueError("One or more permission IDs are invalid")

            before_perms = list(role.get_permission_strings())

            for permission in permissions:
                role.assign_permission(permission)
                await uow.roles.assign_permission(role.id, permission.id)

            after_perms = list(role.get_permission_strings())

            audit = AuditLog.create_success(
                actor_id=actor.id,
                actor_email=str(actor.email),
                actor_roles=actor.get_role_names(),
                action=ActionType.ROLES_PERMISSION_ASSIGN,
                resource="roles",
                resource_id=role.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                before={"permissions": before_perms},
                after={"permissions": after_perms},
                diff={"permissions": {"from": before_perms, "to": after_perms}},
            )
            await uow.audit.log(audit)
            await uow.commit()
            return role


class RemovePermissionsFromRoleUseCase:
    """
    Remove one or more permissions from a role.
    - Logs before/after permission snapshot in audit
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        dto: RemovePermissionsDTO,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> Role:
        async with self._uow as uow:
            role = await uow.roles.get_by_id_with_permissions(dto.role_id)
            if not role or role.is_deleted:
                raise ValueError(f"Role {dto.role_id} not found")

            before_perms = list(role.get_permission_strings())

            for permission_id in dto.permission_ids:
                role.remove_permission(permission_id)
                await uow.roles.remove_permission(role.id, permission_id)

            after_perms = list(role.get_permission_strings())

            audit = AuditLog.create_success(
                actor_id=actor.id,
                actor_email=str(actor.email),
                actor_roles=actor.get_role_names(),
                action=ActionType.ROLES_PERMISSION_REMOVE,
                resource="roles",
                resource_id=role.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                before={"permissions": before_perms},
                after={"permissions": after_perms},
                diff={"permissions": {"from": before_perms, "to": after_perms}},
            )
            await uow.audit.log(audit)
            await uow.commit()
            return role