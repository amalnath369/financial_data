from __future__ import annotations
from types import TracebackType
from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.repositories.uow import AbstractUnitOfWork
from app.core.cache_service import AbstractCacheService
from app.infrastructure.repositories.user_repo import SQLAlchemyUserRepository
from app.infrastructure.repositories.record_repo import SQLAlchemyRecordRepository
from app.infrastructure.repositories.cached_repo import CachedRecordRepository
from app.infrastructure.repositories.category_repo import SQLAlchemyCategoryRepository
from app.infrastructure.repositories.role_permission_repo import (
    SQLAlchemyRoleRepository,
    SQLAlchemyPermissionRepository,
)
from app.infrastructure.repositories.audit_repo import SQLAlchemyAuditRepository


class SQLAlchemyUnitOfWork(AbstractUnitOfWork):
    """
    Concrete Unit of Work.
    Wires all repositories to a single shared session.
    Records repository is wrapped with CachedRecordRepository —
    caching is completely transparent to use cases.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        cache: AbstractCacheService,
    ) -> None:
        self._session_factory = session_factory
        self._cache = cache

    async def __aenter__(self) -> SQLAlchemyUnitOfWork:
        self.session = self._session_factory()

        self.users = SQLAlchemyUserRepository(self.session)
        self.categories = SQLAlchemyCategoryRepository(self.session)
        self.roles = SQLAlchemyRoleRepository(self.session)
        self.permissions = SQLAlchemyPermissionRepository(self.session)
        self.audit = SQLAlchemyAuditRepository(self.session)

        # records wrapped with cache decorator — use cases never know
        self.records = CachedRecordRepository(
            repo=SQLAlchemyRecordRepository(self.session),
            cache=self._cache,
        )

        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()