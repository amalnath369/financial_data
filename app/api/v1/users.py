from __future__ import annotations
import uuid

from fastapi import APIRouter, Depends, Request

from app.api.schemas.base import PaginatedResponse, SuccessResponse
from app.api.schemas.user import (
    AssignRoleRequest,
    ChangeStatusRequest,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.api.v1._mappers import map_user
from app.application.use_cases.users.dtos import (
    AssignRoleDTO,
    ChangeStatusDTO,
    CreateUserDTO,
    GetUsersDTO,
    RemoveRoleDTO,
    UpdateUserDTO,
)
from app.core.containers import (
    get_assign_role_uc,
    get_change_status_uc,
    get_create_user_uc,
    get_delete_user_uc,
    get_get_user_uc,
    get_get_users_uc,
    get_remove_role_uc,
    get_update_user_uc,
)
from app.core.dependencies import get_token_payload, require_permission
from app.core.exceptions import ConflictError, NotFoundError

router = APIRouter(prefix="/users", tags=["users"])


def _meta(request: Request) -> tuple[str, str, str]:
    request_id = request.headers.get("X-Request-ID", "")
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("User-Agent", "")
    return request_id, ip, ua


def _actor(payload: dict):
    """Build a minimal actor stub from token payload for use cases that need actor.id."""
    # Use cases that take `actor: User` need the full entity; those are fetched from DB.
    # Here we only pass actor payload; routers that need full User entity fetch from DB.
    return payload


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    include_deleted: bool = False,
    _: None = Depends(require_permission("users:read")),
    uc=Depends(get_get_users_uc),
) -> PaginatedResponse[UserResponse]:
    users, total = await uc.execute(
        GetUsersDTO(page=page, page_size=page_size, search=search, include_deleted=include_deleted)
    )
    return PaginatedResponse.build(
        items=[map_user(u) for u in users],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreate,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("users:create")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_create_user_uc),
) -> UserResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        user = await uc.execute(
            dto=CreateUserDTO(
                email=body.email,
                password=body.password,
                full_name=body.full_name,
                role_names=body.role_names,
            ),
            actor=actor,
            request_id=request_id,
            ip_address=ip,
            user_agent=ua,
        )
    except ValueError as exc:
        raise ConflictError(str(exc)) from exc
    return map_user(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    _: None = Depends(require_permission("users:read")),
    uc=Depends(get_get_user_uc),
) -> UserResponse:
    try:
        user = await uc.execute(user_id)
    except ValueError as exc:
        raise NotFoundError(str(exc)) from exc
    return map_user(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("users:update")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_update_user_uc),
) -> UserResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        user = await uc.execute(
            dto=UpdateUserDTO(user_id=user_id, full_name=body.full_name),
            actor=actor,
            request_id=request_id,
            ip_address=ip,
            user_agent=ua,
        )
    except ValueError as exc:
        raise NotFoundError(str(exc)) from exc
    return map_user(user)


@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: uuid.UUID,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("users:delete")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_delete_user_uc),
) -> SuccessResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        await uc.execute(user_id=user_id, actor=actor, request_id=request_id, ip_address=ip, user_agent=ua)
    except ValueError as exc:
        raise NotFoundError(str(exc)) from exc
    return SuccessResponse(message="User deleted")


@router.patch("/{user_id}/status", response_model=UserResponse)
async def change_status(
    user_id: uuid.UUID,
    body: ChangeStatusRequest,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("users:update")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_change_status_uc),
) -> UserResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        user = await uc.execute(
            dto=ChangeStatusDTO(user_id=user_id, is_active=body.is_active),
            actor=actor,
            request_id=request_id,
            ip_address=ip,
            user_agent=ua,
        )
    except ValueError as exc:
        raise NotFoundError(str(exc)) from exc
    return map_user(user)


@router.post("/{user_id}/roles", response_model=UserResponse)
async def assign_role(
    user_id: uuid.UUID,
    body: AssignRoleRequest,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("users:update")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_assign_role_uc),
) -> UserResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        user = await uc.execute(
            dto=AssignRoleDTO(user_id=user_id, role_id=body.role_id),
            actor=actor,
            request_id=request_id,
            ip_address=ip,
            user_agent=ua,
        )
    except ValueError as exc:
        raise NotFoundError(str(exc)) from exc
    return map_user(user)


@router.delete("/{user_id}/roles/{role_id}", response_model=UserResponse)
async def remove_role(
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("users:update")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_remove_role_uc),
) -> UserResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        user = await uc.execute(
            dto=RemoveRoleDTO(user_id=user_id, role_id=role_id),
            actor=actor,
            request_id=request_id,
            ip_address=ip,
            user_agent=ua,
        )
    except ValueError as exc:
        raise NotFoundError(str(exc)) from exc
    return map_user(user)
