from __future__ import annotations
import uuid

from app.domain.entities.user import User
from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.enums.action_type import ActionType


class DeleteRecordUseCase:
    """
    Soft delete a financial record.
    - Analysts can only delete their own records
    - Admins can delete any record
    - Logs full before snapshot in audit
    - Invalidates dashboard cache
    """

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        redis,
    ) -> None:
        self._uow = uow
        self._redis = redis

    async def execute(
        self,
        record_id: uuid.UUID,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> None:
        async with self._uow as uow:
            record = await uow.records.get_by_id_with_category(record_id)
            if not record or record.is_deleted:
                raise ValueError(f"Record {record_id} not found")

            # ownership check for analysts
            if not actor.has_permission("users:read") and not record.belongs_to(actor.id):
                raise PermissionError("You can only delete your own records")

            before_snapshot = record.to_dict()

            # domain entity enforces soft delete
            record.soft_delete(deleted_by=actor.id)
            await uow.records.update(record)

            audit = AuditLog.create_success(
                actor_id=actor.id,
                actor_email=str(actor.email),
                actor_roles=actor.get_role_names(),
                action=ActionType.RECORDS_DELETE,
                resource="financial_records",
                resource_id=record.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                before=before_snapshot,
                after=None,
            )
            await uow.audit.log(audit)
            await uow.commit()

        await self._invalidate_cache(str(actor.id))

    async def _invalidate_cache(self, user_id: str) -> None:
        try:
            keys = [
                f"dashboard:summary:{user_id}",
                f"dashboard:categories:{user_id}",
                f"dashboard:trends:{user_id}",
                "dashboard:summary:global",
                "dashboard:categories:global",
            ]
            await self._redis.delete(*keys)
        except Exception:
            pass