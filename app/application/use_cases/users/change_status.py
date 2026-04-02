from __future__ import annotations

from app.domain.entities.user import User
from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.enums.action_type import ActionType
from app.application.use_cases.users.dtos import ChangeStatusDTO


class ChangeUserStatusUseCase:
    """
    Activate or deactivate a user.
    - Cannot change your own status
    - Domain entity enforces business rules
    - Logs before/after status in audit
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        dto: ChangeStatusDTO,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> User:
        if dto.user_id == actor.id:
            raise ValueError("You cannot change your own status")

        async with self._uow as uow:
            user = await uow.users.get_by_id_with_roles(dto.user_id)
            if not user:
                raise ValueError(f"User {dto.user_id} not found")
            if user.is_deleted:
                raise ValueError("Cannot change status of a deleted user")

            before = {"status": user.status.value}

            if dto.is_active:
                user.activate()
                action = ActionType.USERS_ACTIVATE
            else:
                user.deactivate()
                action = ActionType.USERS_DEACTIVATE

            after = {"status": user.status.value}

            await uow.users.update(user)

            audit = AuditLog.create_success(
                actor_id=actor.id,
                actor_email=str(actor.email),
                actor_roles=actor.get_role_names(),
                action=action,
                resource="users",
                resource_id=user.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                before=before,
                after=after,
                diff={"status": {"from": before["status"], "to": after["status"]}},
            )
            await uow.audit.log(audit)
            await uow.commit()
            return user