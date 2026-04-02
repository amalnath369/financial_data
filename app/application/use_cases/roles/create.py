from __future__ import annotations

from app.domain.entities.user import User
from app.domain.entities.role import Role
from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.enums.action_type import ActionType
from app.application.use_cases.roles.dtos import CreateRoleDTO


class CreateRoleUseCase:
    """
    Create a new RBAC role with optional permission assignment.
    - Name must be unique (case-insensitive)
    - All provided permission IDs must exist
    - Logs audit with full snapshot
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        dto: CreateRoleDTO,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> Role:
        async with self._uow as uow:
            # 1. name uniqueness
            if await uow.roles.exists_by_name(dto.name):
                raise ValueError(f"Role {dto.name!r} already exists")

            # 2. validate + load permissions
            permissions = []
            if dto.permission_ids:
                permissions = await uow.permissions.get_by_ids(dto.permission_ids)
                if len(permissions) != len(dto.permission_ids):
                    raise ValueError("One or more permission IDs are invalid")

            # 3. create role
            role = Role.create(name=dto.name, description=dto.description)
            for permission in permissions:
                role.assign_permission(permission)

            await uow.roles.add(role)

            # 4. assign permissions in junction table
            for permission in permissions:
                await uow.roles.assign_permission(role.id, permission.id)

            # 5. audit
            audit = AuditLog.create_success(
                actor_id=actor.id,
                actor_email=str(actor.email),
                actor_roles=actor.get_role_names(),
                action=ActionType.ROLES_CREATE,
                resource="roles",
                resource_id=role.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                after={
                    "id": str(role.id),
                    "name": role.name,
                    "permissions": list(role.get_permission_strings()),
                },
            )
            await uow.audit.log(audit)
            await uow.commit()
            return role