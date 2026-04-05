from __future__ import annotations
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# ── engine ─────────────────────────────────────────────────────────────────

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    # connection pool — production-safe limits
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,          # detect stale connections before use
    echo=settings.DB_ECHO,       # SQL logging in dev only
)

# ── session factory ────────────────────────────────────────────────────────

AsyncSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,      # entities stay usable after commit
    autoflush=False,
    autocommit=False,
)


async def get_session() ->  AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a session per request."""
    async with AsyncSessionFactory() as session:
        yield session