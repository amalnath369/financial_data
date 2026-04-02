from __future__ import annotations

from app.domain.entities.user import User
from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.enums.action_type import ActionType
from app.application.use_cases.users.dtos import AssignRoleDTO, RemoveRoleDTO


class AssignRoleToUserUseCase:
    """
    Assign a role to a user.
    - Role must exist and be active
    - Idempotent — assigning already-assigned role is a no-op
    - Logs before/after role snapshot in audit
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        dto: AssignRoleDTO,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> User:
        async with self._uow as uow:
            user = await uow.users.get_by_id_with_roles(dto.user_id)
            if not user:
                raise ValueError(f"User {dto.user_id} not found")

            role = await uow.roles.get_by_id_with_permissions(dto.role_id)
            if not role:
                raise ValueError(f"Role {dto.role_id} not found")
            if not role.is_active:
                raise ValueError(f"Role {role.name!r} is inactive")

            before_roles = user.get_role_names()

            await uow.users.assign_role(user.id, role.id)
            user.assign_role(role)

            audit = AuditLog.create_success(
                actor_id=actor.id,
                actor_email=str(actor.email),
                actor_roles=actor.get_role_names(),
                action=ActionType.USERS_ROLE_ASSIGN,
                resource="users",
                resource_id=user.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                before={"roles": before_roles},
                after={"roles": user.get_role_names()},
                diff={"roles": {
                    "from": before_roles,
                    "to": user.get_role_names(),
                }},
            )
            await uow.audit.log(audit)
            await uow.commit()
            return user


class RemoveRoleFromUserUseCase:
    """
    Remove a role from a user.
    - Cannot remove last role — user must always have at least one role
    - Logs before/after role snapshot in audit
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        dto: RemoveRoleDTO,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> User:
        async with self._uow as uow:
            user = await uow.users.get_by_id_with_roles(dto.user_id)
            if not user:
                raise ValueError(f"User {dto.user_id} not found")

            if len(user.roles) <= 1:
                raise ValueError(
                    "Cannot remove the last role — "
                    "user must have at least one role"
                )

            before_roles = user.get_role_names()

            await uow.users.remove_role(user.id, dto.role_id)
            user.remove_role(dto.role_id)

            audit = AuditLog.create_success(
                actor_id=actor.id,
                actor_email=str(actor.email),
                actor_roles=actor.get_role_names(),
                action=ActionType.USERS_ROLE_REMOVE,
                resource="users",
                resource_id=user.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                before={"roles": before_roles},
                after={"roles": user.get_role_names()},
                diff={"roles": {
                    "from": before_roles,
                    "to": user.get_role_names(),
                }},
            )
            await uow.audit.log(audit)
            await uow.commit()
            return user