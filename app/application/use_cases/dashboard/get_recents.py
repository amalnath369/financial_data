from __future__ import annotations

from app.domain.entities.user import User
from app.domain.entities.record import FinancialRecord
from app.domain.repositories.uow import AbstractUnitOfWork
from app.application.use_cases.dashboard.dtos import DashboardFilterDTO


class GetRecentActivityUseCase:
    """
    Return the most recent financial records.

    - Admins/analysts see all records
    - Viewers see only their own
    - Eager loads category — no N+1
    - Not cached (recent = must be real-time)
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        dto: DashboardFilterDTO,
        actor: User,
        limit: int = 10,
    ) -> list[FinancialRecord]:
        user_id = dto.user_id
        if not actor.has_permission("users:read"):
            user_id = actor.id

        async with self._uow as uow:
            return await uow.records.get_recent(
                user_id=user_id,
                limit=min(limit, 50),  # cap at 50 to prevent abuse
            )