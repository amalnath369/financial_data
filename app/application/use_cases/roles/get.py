from __future__ import annotations
import uuid

from app.domain.entities.role import Role
from app.domain.repositories.uow import AbstractUnitOfWork
from app.application.use_cases.roles.dtos import GetRolesDTO


class GetRolesUseCase:
    """Paginated list of all roles with permissions loaded."""

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self, dto: GetRolesDTO
    ) -> tuple[list[Role], int]:
        async with self._uow as uow:
            return await uow.roles.get_all(
                page=dto.page,
                page_size=dto.page_size,
                include_inactive=dto.include_inactive,
            )


class GetRoleUseCase:
    """Fetch a single role by ID with permissions loaded."""

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, role_id: uuid.UUID) -> Role:
        async with self._uow as uow:
            role = await uow.roles.get_by_id_with_permissions(role_id)
            if not role or role.is_deleted:
                raise ValueError(f"Role {role_id} not found")
            return role