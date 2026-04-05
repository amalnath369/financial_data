from __future__ import annotations
import uuid
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.audit import AuditLog
from app.domain.enums.action_type import ActionType
from app.domain.repositories.audit_repo import AbstractAuditRepository
from app.infrastructure.database.models.audit import AuditLogModel
from app.infrastructure.repositories.mappers import map_audit


class SQLAlchemyAuditRepository(AbstractAuditRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log(self, audit: AuditLog) -> None:
        m = AuditLogModel(
            id=audit.id,
            actor_id=audit.actor_id,
            actor_email=audit.actor_email,
            actor_roles=audit.actor_roles,
            action=audit.action,
            resource=audit.resource,
            resource_id=audit.resource_id,
            before=audit.before,
            after=audit.after,
            diff=audit.diff,
            request_id=audit.request_id,
            ip_address=audit.ip_address,
            user_agent=audit.user_agent,
            status=audit.status,
            failure_reason=audit.failure_reason,
            timestamp=audit.timestamp,
        )
        self._session.add(m)
        await self._session.flush()

    async def get_by_id(self, id: uuid.UUID) -> AuditLog | None:
        result = await self._session.execute(
            select(AuditLogModel).where(AuditLogModel.id == id)
        )
        m = result.scalar_one_or_none()
        return map_audit(m) if m else None

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
        stmt = select(AuditLogModel)

        if actor_id:
            stmt = stmt.where(AuditLogModel.actor_id == actor_id)
        if resource:
            stmt = stmt.where(AuditLogModel.resource == resource)
        if action:
            stmt = stmt.where(AuditLogModel.action == action)
        if from_timestamp:
            stmt = stmt.where(AuditLogModel.timestamp >= from_timestamp)
        if to_timestamp:
            stmt = stmt.where(AuditLogModel.timestamp <= to_timestamp)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self._session.scalar(count_stmt)

        stmt = stmt.order_by(AuditLogModel.timestamp.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return [map_audit(m) for m in result.scalars().all()], total or 0

    async def get_by_resource(
        self,
        resource: str,
        resource_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        stmt = select(AuditLogModel).where(
            AuditLogModel.resource == resource,
            AuditLogModel.resource_id == resource_id,
        )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self._session.scalar(count_stmt)

        stmt = stmt.order_by(AuditLogModel.timestamp.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return [map_audit(m) for m in result.scalars().all()], total or 0

    # immutability guards
    async def add(self, audit: AuditLog) -> AuditLog:
        await self.log(audit)
        return audit

    async def delete(self, entity: AuditLog) -> None:
        raise NotImplementedError("Audit logs are immutable")

    async def update(self, entity: AuditLog) -> AuditLog:
        raise NotImplementedError("Audit logs are immutable")