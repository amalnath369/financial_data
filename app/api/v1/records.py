from __future__ import annotations
import uuid

from fastapi import APIRouter, Depends, Request

from app.api.schemas.base import PaginatedResponse, SuccessResponse
from app.api.schemas.record import RecordCreate, RecordFilter, RecordResponse, RecordUpdate
from app.api.v1._mappers import map_record
from app.application.use_cases.records.dtos import CreateRecordDTO, GetRecordsDTO, UpdateRecordDTO
from app.core.containers import (
    get_create_record_uc,
    get_delete_record_uc,
    get_get_record_uc,
    get_get_records_uc,
    get_update_record_uc,
)
from app.core.containers import get_get_user_uc
from app.core.dependencies import get_token_payload, require_permission
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/records", tags=["records"])


def _meta(request: Request) -> tuple[str, str, str]:
    return (
        request.headers.get("X-Request-ID", ""),
        request.client.host if request.client else "unknown",
        request.headers.get("User-Agent", ""),
    )


@router.get("", response_model=PaginatedResponse[RecordResponse])
async def list_records(
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("records:read")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_get_records_uc),
    # query params
    user_id: uuid.UUID | None = None,
    record_type: str | None = None,
    category_id: uuid.UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[RecordResponse]:
    from app.domain.enums.enum import RecordType
    from datetime import date as dt_date

    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    dto = GetRecordsDTO(
        user_id=user_id,
        record_type=RecordType(record_type) if record_type else None,
        category_id=category_id,
        date_from=dt_date.fromisoformat(date_from) if date_from else None,
        date_to=dt_date.fromisoformat(date_to) if date_to else None,
        search=search,
        page=page,
        page_size=page_size,
    )
    records, total = await uc.execute(dto=dto, actor=actor)
    return PaginatedResponse.build(
        items=[map_record(r) for r in records],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=RecordResponse, status_code=201)
async def create_record(
    body: RecordCreate,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("records:create")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_create_record_uc),
) -> RecordResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        record = await uc.execute(
            dto=CreateRecordDTO(
                amount=body.amount,
                record_type=body.record_type,
                category_id=body.category_id,
                record_date=body.record_date,
                notes=body.notes,
            ),
            actor=actor,
            request_id=request_id,
            ip_address=ip,
            user_agent=ua,
        )
    except ValueError as exc:
        from app.core.exceptions import ValidationError
        raise ValidationError(str(exc)) from exc
    return map_record(record)


@router.get("/{record_id}", response_model=RecordResponse)
async def get_record(
    record_id: uuid.UUID,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("records:read")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_get_record_uc),
) -> RecordResponse:
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        record = await uc.execute(record_id=record_id, actor=actor)
    except (ValueError, PermissionError) as exc:
        raise NotFoundError(str(exc)) from exc
    return map_record(record)


@router.patch("/{record_id}", response_model=RecordResponse)
async def update_record(
    record_id: uuid.UUID,
    body: RecordUpdate,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("records:update")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_update_record_uc),
) -> RecordResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        record = await uc.execute(
            dto=UpdateRecordDTO(
                record_id=record_id,
                amount=body.amount,
                record_type=body.record_type,
                category_id=body.category_id,
                record_date=body.record_date,
                notes=body.notes,
            ),
            actor=actor,
            request_id=request_id,
            ip_address=ip,
            user_agent=ua,
        )
    except (ValueError, PermissionError) as exc:
        raise NotFoundError(str(exc)) from exc
    return map_record(record)


@router.delete("/{record_id}", response_model=SuccessResponse)
async def delete_record(
    record_id: uuid.UUID,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("records:delete")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_delete_record_uc),
) -> SuccessResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        await uc.execute(
            record_id=record_id,
            actor=actor,
            request_id=request_id,
            ip_address=ip,
            user_agent=ua,
        )
    except (ValueError, PermissionError) as exc:
        raise NotFoundError(str(exc)) from exc
    return SuccessResponse(message="Record deleted")
