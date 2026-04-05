from __future__ import annotations

from app.domain.entities.user import User
from app.domain.entities.role import Role
from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.enums.action_type import ActionType
from app.application.use_cases.roles.dtos import UpdateRoleDTO, SYSTEM_ROLES


class UpdateRoleUseCase:
    """
    Update a role's name, description, or active status.
    - System roles (admin/analyst/viewer) cannot be renamed or deactivated
    - Name uniqueness enforced on rename
    - Diff captured for audit
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        dto: UpdateRoleDTO,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> Role:
        async with self._uow as uow:
            role = await uow.roles.get_by_id_with_permissions(dto.role_id)
            if not role or role.is_deleted:
                raise ValueError(f"Role {dto.role_id} not found")

            # protect system roles
            if role.name in SYSTEM_ROLES:
                if dto.name and dto.name.strip().lower() != role.name:
                    raise ValueError(
                        f"System role {role.name!r} cannot be renamed"
                    )
                if dto.is_active is False:
                    raise ValueError(
                        f"System role {role.name!r} cannot be deactivated"
                    )

            # name uniqueness on rename
            if dto.name and dto.name.strip().lower() != role.name:
                if await uow.roles.exists_by_name(dto.name):
                    raise ValueError(f"Role name {dto.name!r} already exists")

            before = {
                "name": role.name,
                "description": role.description,
                "is_active": role.is_active,
            }

            if dto.name is not None:
                role.name = dto.name.strip().lower()
            if dto.description is not None:
                role.description = dto.description
            if dto.is_active is not None:
                role.is_active = dto.is_active

            await uow.roles.update(role)

            after = {
                "name": role.name,
                "description": role.description,
                "is_active": role.is_active,
            }
            diff = {
                k: {"from": before[k], "to": after[k]}
                for k in before
                if before[k] != after[k]
            }

            audit = AuditLog.create_success(
                actor_id=actor.id,
                actor_email=str(actor.email),
                actor_roles=actor.get_role_names(),
                action=ActionType.ROLES_UPDATE,
                resource="roles",
                resource_id=role.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                before=before,
                after=after,
                diff=diff,
            )
            await uow.audit.log(audit)
            await uow.commit()
            return role