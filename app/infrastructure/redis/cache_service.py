from __future__ import annotations

from redis.asyncio import Redis

from app.core.cache_service import AbstractCacheService


class RedisCacheService(AbstractCacheService):
    """
    Redis-backed implementation of AbstractCacheService.

    All methods catch every exception so a Redis failure
    never propagates to use cases or repositories.
    """

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        try:
            return await self._client.get(key)
        except Exception:
            return None

    async def set(self, key: str, value: str, ttl: int) -> None:
        try:
            await self._client.setex(key, ttl, value)
        except Exception:
            pass

    async def delete(self, *keys: str) -> None:
        try:
            if keys:
                await self._client.delete(*keys)
        except Exception:
            pass

    async def keys(self, pattern: str) -> list[str]:
        try:
            return await self._client.keys(pattern)
        except Exception:
            return []

    async def incr(self, key: str) -> int:
        try:
            return await self._client.incr(key)
        except Exception:
            return 0

    async def expire(self, key: str, seconds: int) -> None:
        try:
            await self._client.expire(key, seconds)
        except Exception:
            pass
