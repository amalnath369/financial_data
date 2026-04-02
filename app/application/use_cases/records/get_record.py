from __future__ import annotations
import uuid

from app.domain.entities.user import User
from app.domain.entities.record import FinancialRecord
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.repositories.record_repo import RecordFilters
from app.application.use_cases.records.dtos import GetRecordsDTO


class GetRecordUseCase:
    """
    Fetch a single record by ID.
    - Analysts and admins can fetch any record
    - Viewers can only fetch their own records
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        record_id: uuid.UUID,
        actor: User,
    ) -> FinancialRecord:
        async with self._uow as uow:
            record = await uow.records.get_by_id_with_category(record_id)
            if not record or record.is_deleted:
                raise ValueError(f"Record {record_id} not found")

            # ownership check for viewers
            if not actor.has_permission("records:read") and not record.belongs_to(actor.id):
                raise PermissionError("You can only view your own records")

            return record


class GetRecordsUseCase:
    """
    Paginated, filtered, searchable record list.
    - Admins + analysts see all records (or filter by user_id)
    - Viewers only see their own records
    - Single query with eager loading — no N+1
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        dto: GetRecordsDTO,
        actor: User,
    ) -> tuple[list[FinancialRecord], int]:
        async with self._uow as uow:
            # viewers are always scoped to their own records
            user_id = dto.user_id
            if not actor.has_permission("records:read"):
                user_id = actor.id

            filters = RecordFilters(
                user_id=user_id,
                record_type=dto.record_type,
                category_id=dto.category_id,
                date_from=dto.date_from,
                date_to=dto.date_to,
                min_amount=dto.min_amount,
                max_amount=dto.max_amount,
                search=dto.search,
                page=dto.page,
                page_size=dto.page_size,
            )
            return await uow.records.get_all(filters)