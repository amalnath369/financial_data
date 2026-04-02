from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
import uuid

T = TypeVar("T")


class AbstractBaseRepository(ABC, Generic[T]):
    """
    Generic base repository interface.
    All concrete repositories implement these basic operations.
    """

    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> T | None:
        """Fetch a single entity by primary key. Returns None if not found."""
        raise NotImplementedError

    @abstractmethod
    async def add(self, entity: T) -> T:
        """Persist a new entity. Returns the saved entity."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Persist changes to an existing entity. Returns the updated entity."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, entity: T) -> None:
        """Hard delete — use only for junction tables or tokens."""
        raise NotImplementedError