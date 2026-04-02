from __future__ import annotations
import uuid

from app.domain.entities.user import User
from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.enums.action_type import ActionType


class DeleteUserUseCase:
    """
    Soft delete a user.
    - Cannot delete yourself
    - Cannot delete already deleted user
    - Logs full before snapshot in audit
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        user_id: uuid.UUID,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> None:
        if user_id == actor.id:
            raise ValueError("You cannot delete your own account")

        async with self._uow as uow:
            user = await uow.users.get_by_id_with_roles(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")

            before = {
                "id": str(user.id),
                "email": str(user.email),
                "full_name": user.full_name,
                "status": user.status.value,
                "roles": user.get_role_names(),
            }

            # domain entity enforces soft delete logic
            user.soft_delete(deleted_by=actor.id)
            await uow.users.update(user)

            audit = AuditLog.create_success(
                actor_id=actor.id,
                actor_email=str(actor.email),
                actor_roles=actor.get_role_names(),
                action=ActionType.USERS_DELETE,
                resource="users",
                resource_id=user.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                before=before,
                after=None,
            )
            await uow.audit.log(audit)
            await uow.commit()