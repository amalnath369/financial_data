from __future__ import annotations
import uuid

from app.domain.entities.user import User
from app.domain.repositories.uow import AbstractUnitOfWork
from app.application.use_cases.users.dtos import GetUsersDTO


class GetUserUseCase:
    """
    Fetch a single user by ID with roles eagerly loaded.
    Raises ValueError if not found.
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, user_id: uuid.UUID) -> User:
        async with self._uow as uow:
            user = await uow.users.get_by_id_with_roles(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            return user


class GetUsersUseCase:
    """
    Paginated list of users with optional search.
    Returns (users, total_count).
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self, dto: GetUsersDTO
    ) -> tuple[list[User], int]:
        async with self._uow as uow:
            return await uow.users.get_all(
                page=dto.page,
                page_size=dto.page_size,
                is_deleted=dto.include_deleted,
                search=dto.search,
            )