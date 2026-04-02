from __future__ import annotations

from app.domain.entities.user import User
from app.domain.entities.category import Category
from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.enums.action_type import ActionType
from app.application.use_cases.categories.dtos import UpdateCategoryDTO


class UpdateCategoryUseCase:
    """
    Update a category's name, description, or active status.
    - System categories are protected — domain entity raises ValueError
    - Name uniqueness enforced on rename
    - Diff captured for audit
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        dto: UpdateCategoryDTO,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> Category:
        async with self._uow as uow:
            category = await uow.categories.get_by_id(dto.category_id)
            if not category or category.is_deleted:
                raise ValueError(f"Category {dto.category_id} not found")

            # check name uniqueness only if name is changing
            if dto.name and dto.name.strip().lower() != category.name.lower():
                if await uow.categories.exists_by_name(dto.name):
                    raise ValueError(
                        f"Category name {dto.name!r} already exists"
                    )

            before = {
                "name": category.name,
                "description": category.description,
                "is_active": category.is_active,
            }

            # domain entity enforces is_system protection
            category.update(
                name=dto.name,
                description=dto.description,
                is_active=dto.is_active,
            )
            await uow.categories.update(category)

            after = {
                "name": category.name,
                "description": category.description,
                "is_active": category.is_active,
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
                action=ActionType.CATEGORIES_UPDATE,
                resource="categories",
                resource_id=category.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                before=before,
                after=after,
                diff=diff,
            )
            await uow.audit.log(audit)
            await uow.commit()
            return category