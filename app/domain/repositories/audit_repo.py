from __future__ import annotations
from abc import abstractmethod
from datetime import datetime
import uuid

from app.domain.repositories.base import AbstractBaseRepository
from app.domain.entities.audit import AuditLog
from app.domain.enums.action_type import ActionType


class AbstractAuditRepository(AbstractBaseRepository[AuditLog]):
    """
    Audit log repository interface.
    - Write-heavy, read-rarely
    - No update or hard delete — audit logs are immutable
    - Supports filtering for admin audit trail views
    """

    @abstractmethod
    async def log(self, audit: AuditLog) -> None:
        """Persist an audit log entry. Called inside UoW transactions."""
        raise NotImplementedError

    @abstractmethod
    async def get_all(
        self,
        page: int = 1,
        page_size: int = 50,
        actor_id: uuid.UUID | None = None,
        resource: str | None = None,
        action: ActionType | None = None,
        from_timestamp: datetime | None = None,
        to_timestamp: datetime | None = None,
    ) -> tuple[list[AuditLog], int]:
        """
        Paginated, filtered audit log listing for admin views.
        Returns (logs, total_count).
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_resource(
        self,
        resource: str,
        resource_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        """
        Fetch audit history for a specific resource instance.
        e.g. all changes to a specific financial record.
        """
        raise NotImplementedError

    # Override base methods to make clear audit logs are immutable

    async def update(self, entity: AuditLog) -> AuditLog:
        raise NotImplementedError("Audit logs are immutable — update not allowed")

    async def delete(self, entity: AuditLog) -> None:
        raise NotImplementedError("Audit logs are immutable — delete not allowed")