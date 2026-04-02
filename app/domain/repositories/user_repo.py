from __future__ import annotations
from abc import abstractmethod
from typing import Any
import uuid

from app.domain.repositories.base import AbstractBaseRepository
from app.domain.entities.user import User
from app.domain.value_objects.email import Email


class AbstractUserRepository(AbstractBaseRepository[User]):
    """
    User-specific repository interface.
    Extends base CRUD with user-domain queries.
    """

    @abstractmethod
    async def get_by_email(self, email: Email) -> User | None:
        """Fetch a user by their email address."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id_with_roles(self, id: uuid.UUID) -> User | None:
        """Fetch a user with roles + permissions eagerly loaded."""
        raise NotImplementedError

    @abstractmethod
    async def exists_by_email(self, email: Email) -> bool:
        """Check if a user with this email already exists."""
        raise NotImplementedError

    @abstractmethod
    async def get_all(
        self,
        page: int,
        page_size: int,
        is_deleted: bool = False,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        """
        Paginated list of users.
        Returns (users, total_count).
        """
        raise NotImplementedError

    @abstractmethod
    async def assign_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        """Assign a role to a user via user_roles junction."""
        raise NotImplementedError

    @abstractmethod
    async def remove_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        """Remove a role from a user."""
        raise NotImplementedError

    @abstractmethod
    async def get_active_by_id(self, id: uuid.UUID) -> User | None:
        """Fetch only if user is active and not deleted."""
        raise NotImplementedError