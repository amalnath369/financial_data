from __future__ import annotations
import uuid

from app.domain.entities.user import User
from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.enums.action_type import ActionType


class DeleteCategoryUseCase:
    """
    Soft delete a category.
    - System categories are protected — domain entity raises ValueError
    - Logs full before snapshot in audit
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        category_id: uuid.UUID,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> None:
        async with self._uow as uow:
            category = await uow.categories.get_by_id(category_id)
            if not category or category.is_deleted:
                raise ValueError(f"Category {category_id} not found")

            before = {
                "id": str(category.id),
                "name": category.name,
                "type": category.category_type.value,
                "is_system": category.is_system,
            }

            # domain entity raises ValueError if is_system=True
            category.soft_delete(deleted_by=actor.id)
            await uow.categories.update(category)

            audit = AuditLog.create_success(
                actor_id=actor.id,
                actor_email=str(actor.email),
                actor_roles=actor.get_role_names(),
                action=ActionType.CATEGORIES_DELETE,
                resource="categories",
                resource_id=category.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                before=before,
                after=None,
            )
            await uow.audit.log(audit)
            await uow.commit()