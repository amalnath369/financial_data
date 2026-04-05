from __future__ import annotations

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings

# ── client ─────────────────────────────────────────────────────────────────

_redis_client: Redis | None = None


async def get_redis() -> Redis:
    """
    Returns the shared async Redis client.
    Initialised once on first call.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=False,  # fail fast — callers handle gracefully
        )
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


# ── safe helpers ───────────────────────────────────────────────────────────
# Use these when Redis failure must never crash the application.

async def safe_get(key: str) -> str | None:
    try:
        client = await get_redis()
        return await client.get(key)
    except RedisError:
        return None


async def safe_set(key: str, value: str, ttl: int | None = None) -> bool:
    try:
        client = await get_redis()
        if ttl:
            await client.setex(key, ttl, value)
        else:
            await client.set(key, value)
        return True
    except RedisError:
        return False


async def safe_delete(*keys: str) -> bool:
    try:
        client = await get_redis()
        await client.delete(*keys)
        return True
    except RedisError:
        return False