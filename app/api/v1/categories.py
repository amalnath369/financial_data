from __future__ import annotations
import uuid

from fastapi import APIRouter, Depends, Request

from app.api.schemas.base import PaginatedResponse, SuccessResponse
from app.api.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.api.v1._mappers import map_category
from app.application.use_cases.categories.dtos import CreateCategoryDTO, GetCategoriesDTO, UpdateCategoryDTO
from app.core.containers import (
    get_create_category_uc,
    get_delete_category_uc,
    get_get_categories_uc,
    get_get_category_uc,
    get_update_category_uc,
    get_get_user_uc,
)
from app.core.dependencies import get_token_payload, require_permission
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.enums.enum import CategoryType

router = APIRouter(prefix="/categories", tags=["categories"])


def _meta(request: Request) -> tuple[str, str, str]:
    return (
        request.headers.get("X-Request-ID", ""),
        request.client.host if request.client else "unknown",
        request.headers.get("User-Agent", ""),
    )


@router.get("", response_model=PaginatedResponse[CategoryResponse])
async def list_categories(
    _: None = Depends(require_permission("categories:read")),
    uc=Depends(get_get_categories_uc),
    category_type: str | None = None,
    include_inactive: bool = False,
    page: int = 1,
    page_size: int = 50,
) -> PaginatedResponse[CategoryResponse]:
    cats, total = await uc.execute(
        GetCategoriesDTO(
            category_type=CategoryType(category_type) if category_type else None,
            include_inactive=include_inactive,
            page=page,
            page_size=page_size,
        )
    )
    return PaginatedResponse.build(
        items=[map_category(c) for c in cats],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(
    body: CategoryCreate,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("categories:create")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_create_category_uc),
) -> CategoryResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        cat = await uc.execute(
            dto=CreateCategoryDTO(
                name=body.name,
                category_type=body.category_type,
                description=body.description,
            ),
            actor=actor,
            request_id=request_id,
            ip_address=ip,
            user_agent=ua,
        )
    except ValueError as exc:
        raise ConflictError(str(exc)) from exc
    return map_category(cat)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: uuid.UUID,
    _: None = Depends(require_permission("categories:read")),
    uc=Depends(get_get_category_uc),
) -> CategoryResponse:
    try:
        cat = await uc.execute(category_id)
    except ValueError as exc:
        raise NotFoundError(str(exc)) from exc
    return map_category(cat)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    body: CategoryUpdate,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("categories:update")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_update_category_uc),
) -> CategoryResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        cat = await uc.execute(
            dto=UpdateCategoryDTO(
                category_id=category_id,
                name=body.name,
                description=body.description,
                is_active=body.is_active,
            ),
            actor=actor,
            request_id=request_id,
            ip_address=ip,
            user_agent=ua,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    return map_category(cat)


@router.delete("/{category_id}", response_model=SuccessResponse)
async def delete_category(
    category_id: uuid.UUID,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("categories:delete")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_delete_category_uc),
) -> SuccessResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        await uc.execute(
            category_id=category_id,
            actor=actor,
            request_id=request_id,
            ip_address=ip,
            user_agent=ua,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    return SuccessResponse(message="Category deleted")
