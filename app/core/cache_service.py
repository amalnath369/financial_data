from __future__ import annotations
from abc import ABC, abstractmethod


class AbstractCacheService(ABC):
    """
    Cache service interface — lives in core layer.

    Use cases and repositories depend only on this interface.
    The concrete implementation (Redis) lives in infrastructure.

    All operations degrade gracefully: implementations must never
    let a cache failure propagate to the caller.
    """

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Return the cached string value, or None on miss/failure."""
        raise NotImplementedError

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int) -> None:
        """Store value with TTL in seconds. Silently no-ops on failure."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, *keys: str) -> None:
        """Delete one or more keys. Silently no-ops on failure."""
        raise NotImplementedError

    @abstractmethod
    async def keys(self, pattern: str) -> list[str]:
        """Return all keys matching a glob pattern. Returns [] on failure."""
        raise NotImplementedError

    @abstractmethod
    async def incr(self, key: str) -> int:
        """Atomically increment key and return new value. Returns 0 on failure."""
        raise NotImplementedError

    @abstractmethod
    async def expire(self, key: str, seconds: int) -> None:
        """Set a TTL on an existing key. Silently no-ops on failure."""
        raise NotImplementedError
