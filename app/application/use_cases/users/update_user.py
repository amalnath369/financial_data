from __future__ import annotations

from app.domain.entities.user import User
from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.enums.action_type import ActionType
from app.application.use_cases.users.dtos import UpdateUserDTO


class UpdateUserUseCase:
    """
    Update a user's profile fields.
    - Captures before/after diff for audit
    - Only updates provided fields
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        dto: UpdateUserDTO,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> User:
        async with self._uow as uow:
            user = await uow.users.get_by_id_with_roles(dto.user_id)
            if not user:
                raise ValueError(f"User {dto.user_id} not found")

            # snapshot before
            before = {"full_name": user.full_name}

            # apply updates
            user.update_profile(full_name=dto.full_name)
            await uow.users.update(user)

            # snapshot after + diff
            after = {"full_name": user.full_name}
            diff = {
                k: {"from": before[k], "to": after[k]}
                for k in before
                if before[k] != after[k]
            }

            audit = AuditLog.create_success(
                actor_id=actor.id,
                actor_email=str(actor.email),
                actor_roles=actor.get_role_names(),
                action=ActionType.USERS_UPDATE,
                resource="users",
                resource_id=user.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                before=before,
                after=after,
                diff=diff,
            )
            await uow.audit.log(audit)
            await uow.commit()
            return user