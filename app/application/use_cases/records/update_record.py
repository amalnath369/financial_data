from __future__ import annotations

from app.domain.entities.user import User
from app.domain.entities.record import FinancialRecord
from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.value_objects.money import Money
from app.domain.enums.action_type import ActionType
from app.application.use_cases.records.dtos import UpdateRecordDTO


class UpdateRecordUseCase:
    """
    Update an existing financial record.
    - Analysts can only update their own records
    - Admins can update any record
    - Returns diff from entity.update() directly into audit
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
        dto: UpdateRecordDTO,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> FinancialRecord:
        async with self._uow as uow:
            record = await uow.records.get_by_id_with_category(dto.record_id)
            if not record or record.is_deleted:
                raise ValueError(f"Record {dto.record_id} not found")

            # ownership check for analysts
            if not actor.has_permission("users:read") and not record.belongs_to(actor.id):
                raise PermissionError("You can only update your own records")

            # validate new category if provided
            if dto.category_id:
                category = await uow.categories.get_by_id(dto.category_id)
                if not category or not category.is_active or category.is_deleted:
                    raise ValueError(f"Category {dto.category_id} not found or inactive")

            before_snapshot = record._snapshot()

            # entity.update() returns diff automatically
            diff = record.update(
                amount=Money(dto.amount) if dto.amount is not None else None,
                record_type=dto.record_type,
                category_id=dto.category_id,
                record_date=dto.record_date,
                notes=dto.notes,
            )

            await uow.records.update(record)

            audit = AuditLog.create_success(
                actor_id=actor.id,
                actor_email=str(actor.email),
                actor_roles=actor.get_role_names(),
                action=ActionType.RECORDS_UPDATE,
                resource="financial_records",
                resource_id=record.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                before=before_snapshot,
                after=record._snapshot(),
                diff=diff,
            )
            await uow.audit.log(audit)
            await uow.commit()

        await self._invalidate_cache(str(actor.id))
        return record

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