from __future__ import annotations
from abc import abstractmethod
import uuid

from app.domain.repositories.base import AbstractBaseRepository
from app.domain.entities.role import Role


class AbstractRoleRepository(AbstractBaseRepository[Role]):
    """
    Role-specific repository interface.
    """

    @abstractmethod
    async def get_by_name(self, name: str) -> Role | None:
        """Fetch a role by its name (case-insensitive)."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id_with_permissions(self, id: uuid.UUID) -> Role | None:
        """Fetch a role with permissions eagerly loaded."""
        raise NotImplementedError

    @abstractmethod
    async def get_all(
        self,
        page: int = 1,
        page_size: int = 50,
        include_inactive: bool = False,
    ) -> tuple[list[Role], int]:
        """
        Paginated list of roles with permissions loaded.
        Returns (roles, total_count).
        """
        raise NotImplementedError

    @abstractmethod
    async def exists_by_name(self, name: str) -> bool:
        """Check for name uniqueness before create/update."""
        raise NotImplementedError

    @abstractmethod
    async def assign_permission(
        self, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> None:
        """Assign a permission to a role via role_permissions junction."""
        raise NotImplementedError

    @abstractmethod
    async def remove_permission(
        self, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> None:
        """Remove a permission from a role."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_ids(self, ids: list[uuid.UUID]) -> list[Role]:
        """Batch fetch roles by IDs."""
        raise NotImplementedError