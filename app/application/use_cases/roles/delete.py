from __future__ import annotations
import uuid

from app.domain.entities.user import User
from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.enums.action_type import ActionType
from app.application.use_cases.roles.dtos import SYSTEM_ROLES


class DeleteRoleUseCase:
    """
    Soft delete a role.
    - System roles (admin/analyst/viewer) cannot be deleted
    - Logs full before snapshot in audit
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        role_id: uuid.UUID,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> None:
        async with self._uow as uow:
            role = await uow.roles.get_by_id_with_permissions(role_id)
            if not role or role.is_deleted:
                raise ValueError(f"Role {role_id} not found")

            if role.name in SYSTEM_ROLES:
                raise ValueError(
                    f"System role {role.name!r} cannot be deleted"
                )

            before = {
                "id": str(role.id),
                "name": role.name,
                "permissions": list(role.get_permission_strings()),
            }

            role.soft_delete(deleted_by=actor.id)
            await uow.roles.update(role)

            audit = AuditLog.create_success(
                actor_id=actor.id,
                actor_email=str(actor.email),
                actor_roles=actor.get_role_names(),
                action=ActionType.ROLES_DELETE,
                resource="roles",
                resource_id=role.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                before=before,
                after=None,
            )
            await uow.audit.log(audit)
            await uow.commit()