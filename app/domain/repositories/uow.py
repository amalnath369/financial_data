from __future__ import annotations
from abc import ABC, abstractmethod
from types import TracebackType
from typing import Type

from app.domain.repositories.user_repo import AbstractUserRepository
from app.domain.repositories.record_repo import AbstractRecordRepository
from app.domain.repositories.category_repo import AbstractCategoryRepository
from app.domain.repositories.role_repo import AbstractRoleRepository
from app.domain.repositories.permission_repo import AbstractPermissionRepository
from app.domain.repositories.audit_repo import AbstractAuditRepository


class AbstractUnitOfWork(ABC):
    """
    Unit of Work interface — lives in domain layer.

    Guarantees that all repository operations within a single
    use case execute in one atomic transaction.

    Usage:
        async with uow:
            await uow.records.add(record)
            await uow.audit.log(audit_entry)
            await uow.commit()
            # on any exception → auto rollback via __aexit__
    """

    users: AbstractUserRepository
    records: AbstractRecordRepository
    categories: AbstractCategoryRepository
    roles: AbstractRoleRepository
    permissions: AbstractPermissionRepository
    audit: AbstractAuditRepository

    # ── context manager ────────────────────────────────────────────────────

    @abstractmethod
    async def __aenter__(self) -> AbstractUnitOfWork:
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Auto rollback on any unhandled exception."""
        raise NotImplementedError

    # ── transaction control ────────────────────────────────────────────────

    @abstractmethod
    async def commit(self) -> None:
        """Commit all pending changes in the current session."""
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback all pending changes in the current session."""
        raise NotImplementedError