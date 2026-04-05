from __future__ import annotations
import uuid

from app.domain.entities.user import User
from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.enums.action_type import ActionType
from app.core.cache_service import AbstractCacheService


class DeleteRecordUseCase:
    """
    Soft delete a financial record.
    - Only actors with records:delete can delete others' records
    - Logs full before snapshot in audit
    - Invalidates dashboard cache
    """

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        cache: AbstractCacheService,
    ) -> None:
        self._uow = uow
        self._cache = cache

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

            # ownership check — only actors with records:delete can delete others' records
            if not actor.has_permission("records:delete") and not record.belongs_to(actor.id):
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
        user_keys = await self._cache.keys(f"dashboard:*:{user_id}:*")
        global_keys = await self._cache.keys("dashboard:*:global:*")
        all_keys = user_keys + global_keys
        if all_keys:
            await self._cache.delete(*all_keys)