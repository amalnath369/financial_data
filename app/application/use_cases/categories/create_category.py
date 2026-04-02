from __future__ import annotations

from app.domain.entities.user import User
from app.domain.entities.category import Category
from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.enums.action_type import ActionType
from app.application.use_cases.categories.dtos import CreateCategoryDTO


class CreateCategoryUseCase:
    """
    Create a new user-defined category.
    - Name must be unique (case-insensitive)
    - is_system always False for API-created categories
    - Logs audit with full after snapshot
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        dto: CreateCategoryDTO,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> Category:
        async with self._uow as uow:
            # 1. name uniqueness
            if await uow.categories.exists_by_name(dto.name):
                raise ValueError(
                    f"Category with name {dto.name!r} already exists"
                )

            # 2. create
            category = Category.create(
                name=dto.name,
                category_type=dto.category_type,
                description=dto.description,
                created_by=actor.id,
                is_system=False,
            )
            await uow.categories.add(category)

            # 3. audit
            audit = AuditLog.create_success(
                actor_id=actor.id,
                actor_email=str(actor.email),
                actor_roles=actor.get_role_names(),
                action=ActionType.CATEGORIES_CREATE,
                resource="categories",
                resource_id=category.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                after={
                    "id": str(category.id),
                    "name": category.name,
                    "type": category.category_type.value,
                    "is_system": category.is_system,
                },
            )
            await uow.audit.log(audit)
            await uow.commit()
            return category