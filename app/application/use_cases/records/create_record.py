from __future__ import annotations

from app.domain.entities.user import User
from app.domain.entities.record import FinancialRecord
from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.value_objects.money import Money
from app.domain.enums.action_type import ActionType
from app.application.use_cases.records.dtos import CreateRecordDTO


class CreateRecordUseCase:
    """
    Create a new financial record.
    - Validates category exists and is active
    - Creates record using Money value object (validates amount)
    - Invalidates dashboard Redis cache via event
    - Logs full after snapshot in audit
    - All atomic in one UoW transaction
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
        dto: CreateRecordDTO,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> FinancialRecord:
        async with self._uow as uow:
            # 1. validate category
            category = await uow.categories.get_by_id(dto.category_id)
            if not category or not category.is_active or category.is_deleted:
                raise ValueError(f"Category {dto.category_id} not found or inactive")

            # 2. create record — Money validates amount
            record = FinancialRecord.create(
                user_id=actor.id,
                amount=Money(dto.amount),
                record_type=dto.record_type,
                category_id=dto.category_id,
                record_date=dto.record_date,
                notes=dto.notes,
            )
            record.category_name = category.name

            await uow.records.add(record)

            # 3. audit
            audit = AuditLog.create_success(
                actor_id=actor.id,
                actor_email=str(actor.email),
                actor_roles=actor.get_role_names(),
                action=ActionType.RECORDS_CREATE,
                resource="financial_records",
                resource_id=record.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                after=record.to_dict(),
            )
            await uow.audit.log(audit)
            await uow.commit()

        # 4. invalidate dashboard cache after commit
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
            if keys:
                await self._redis.delete(*keys)
        except Exception:
            pass  