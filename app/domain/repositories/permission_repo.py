from __future__ import annotations
from abc import abstractmethod
import uuid

from app.domain.repositories.base import AbstractBaseRepository
from app.domain.entities.permission import Permission


class AbstractPermissionRepository(AbstractBaseRepository[Permission]):
    """
    Permission-specific repository interface.
    Permissions are seeded at startup and mostly read-only at runtime.
    """

    @abstractmethod
    async def get_by_codename(self, codename: str) -> Permission | None:
        """
        Fetch a permission by its codename string e.g. 'records:create'.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> list[Permission]:
        """Return all permissions — no pagination needed (small fixed set)."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_ids(self, ids: list[uuid.UUID]) -> list[Permission]:
        """Batch fetch permissions by IDs."""
        raise NotImplementedError

    @abstractmethod
    async def exists_by_codename(self, codename: str) -> bool:
        """Check if a permission with this codename already exists."""
        raise NotImplementedError

    @abstractmethod
    async def bulk_create(self, permissions: list[Permission]) -> None:
        """
        Used during seeding to insert all permissions in one operation.
        Skips already-existing codenames.
        """
        raise NotImplementedError