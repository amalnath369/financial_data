from __future__ import annotations
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Request

from app.api.schemas.dashboard import CategoryTotalResponse, SummaryResponse, TrendPointResponse
from app.api.schemas.record import RecordResponse
from app.api.v1._mappers import map_record
from app.application.use_cases.dashboard.dtos import DashboardFilterDTO, TrendsFilterDTO
from app.core.containers import (
    get_category_totals_uc,
    get_get_user_uc,
    get_recents_uc,
    get_summary_uc,
    get_trends_uc,
)
from app.core.dependencies import get_token_payload, require_permission

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("dashboard:read")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_summary_uc),
    user_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> SummaryResponse:
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    result = await uc.execute(
        dto=DashboardFilterDTO(user_id=user_id, date_from=date_from, date_to=date_to),
        actor=actor,
    )
    return SummaryResponse(
        total_income=result.total_income,
        total_expense=result.total_expense,
        net_balance=result.net_balance,
        total_records=result.total_records,
        cached=result.cached,
    )


@router.get("/categories", response_model=list[CategoryTotalResponse])
async def get_category_totals(
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("dashboard:read")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_category_totals_uc),
    user_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[CategoryTotalResponse]:
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    totals = await uc.execute(
        dto=DashboardFilterDTO(user_id=user_id, date_from=date_from, date_to=date_to),
        actor=actor,
    )
    return [
        CategoryTotalResponse(
            category_id=t.category_id,
            category_name=t.category_name,
            record_type=t.record_type,
            total=t.total,
            count=t.count,
        )
        for t in totals
    ]


@router.get("/trends", response_model=list[TrendPointResponse])
async def get_trends(
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("dashboard:read")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_trends_uc),
    period: str = "monthly",
    user_id: uuid.UUID | None = None,
    limit: int = 12,
) -> list[TrendPointResponse]:
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    trends = await uc.execute(
        dto=TrendsFilterDTO(period=period, user_id=user_id, limit=limit),
        actor=actor,
    )
    return [
        TrendPointResponse(
            period=t.period,
            record_type=t.record_type,
            total=t.total,
            count=t.count,
        )
        for t in trends
    ]


@router.get("/recent", response_model=list[RecordResponse])
async def get_recent(
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("dashboard:read")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_recents_uc),
    user_id: uuid.UUID | None = None,
    limit: int = 10,
) -> list[RecordResponse]:
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    records = await uc.execute(
        dto=DashboardFilterDTO(user_id=user_id),
        actor=actor,
        limit=limit,
    )
    return [map_record(r) for r in records]
