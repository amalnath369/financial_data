from __future__ import annotations
import uuid

from fastapi import APIRouter, Depends, Request

from app.api.schemas.base import PaginatedResponse, SuccessResponse
from app.api.schemas.role import AssignPermissionsRequest, RoleCreate, RoleResponse, RoleUpdate
from app.api.v1._mappers import map_role_detail
from app.application.use_cases.roles.dtos import (
    AssignPermissionsDTO,
    CreateRoleDTO,
    GetRolesDTO,
    RemovePermissionsDTO,
    UpdateRoleDTO,
)
from app.core.containers import (
    get_assign_perms_uc,
    get_create_role_uc,
    get_delete_role_uc,
    get_get_role_uc,
    get_get_roles_uc,
    get_get_user_uc,
    get_remove_perms_uc,
    get_update_role_uc,
)
from app.core.dependencies import get_token_payload, require_permission
from app.core.exceptions import ConflictError, NotFoundError, ValidationError

router = APIRouter(prefix="/roles", tags=["roles"])


def _meta(request: Request) -> tuple[str, str, str]:
    return (
        request.headers.get("X-Request-ID", ""),
        request.client.host if request.client else "unknown",
        request.headers.get("User-Agent", ""),
    )


@router.get("", response_model=PaginatedResponse[RoleResponse])
async def list_roles(
    _: None = Depends(require_permission("roles:manage")),
    uc=Depends(get_get_roles_uc),
    include_inactive: bool = False,
    page: int = 1,
    page_size: int = 50,
) -> PaginatedResponse[RoleResponse]:
    roles, total = await uc.execute(
        GetRolesDTO(include_inactive=include_inactive, page=page, page_size=page_size)
    )
    return PaginatedResponse.build(
        items=[map_role_detail(r) for r in roles],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=RoleResponse, status_code=201)
async def create_role(
    body: RoleCreate,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("roles:manage")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_create_role_uc),
) -> RoleResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        role = await uc.execute(
            dto=CreateRoleDTO(
                name=body.name,
                description=body.description,
                permission_ids=body.permission_ids,
            ),
            actor=actor,
            request_id=request_id,
            ip_address=ip,
            user_agent=ua,
        )
    except ValueError as exc:
        raise ConflictError(str(exc)) from exc
    return map_role_detail(role)


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: uuid.UUID,
    _: None = Depends(require_permission("roles:manage")),
    uc=Depends(get_get_role_uc),
) -> RoleResponse:
    try:
        role = await uc.execute(role_id)
    except ValueError as exc:
        raise NotFoundError(str(exc)) from exc
    return map_role_detail(role)


@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: uuid.UUID,
    body: RoleUpdate,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("roles:manage")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_update_role_uc),
) -> RoleResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        role = await uc.execute(
            dto=UpdateRoleDTO(
                role_id=role_id,
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
    return map_role_detail(role)


@router.delete("/{role_id}", response_model=SuccessResponse)
async def delete_role(
    role_id: uuid.UUID,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("roles:manage")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_delete_role_uc),
) -> SuccessResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        await uc.execute(
            role_id=role_id,
            actor=actor,
            request_id=request_id,
            ip_address=ip,
            user_agent=ua,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    return SuccessResponse(message="Role deleted")


@router.post("/{role_id}/permissions", response_model=RoleResponse)
async def assign_permissions(
    role_id: uuid.UUID,
    body: AssignPermissionsRequest,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("roles:manage")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_assign_perms_uc),
) -> RoleResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        role = await uc.execute(
            dto=AssignPermissionsDTO(role_id=role_id, permission_ids=body.permission_ids),
            actor=actor,
            request_id=request_id,
            ip_address=ip,
            user_agent=ua,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    return map_role_detail(role)


@router.delete("/{role_id}/permissions", response_model=RoleResponse)
async def remove_permissions(
    role_id: uuid.UUID,
    body: AssignPermissionsRequest,
    request: Request,
    payload: dict = Depends(get_token_payload),
    _: None = Depends(require_permission("roles:manage")),
    actor_uc=Depends(get_get_user_uc),
    uc=Depends(get_remove_perms_uc),
) -> RoleResponse:
    request_id, ip, ua = _meta(request)
    actor = await actor_uc.execute(uuid.UUID(payload["sub"]))
    try:
        role = await uc.execute(
            dto=RemovePermissionsDTO(role_id=role_id, permission_ids=body.permission_ids),
            actor=actor,
            request_id=request_id,
            ip_address=ip,
            user_agent=ua,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    return map_role_detail(role)
