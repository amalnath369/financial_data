from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response

from app.application.use_cases.auth.dtos import LoginDTO, LogoutDTO, RefreshDTO, RegisterDTO
from app.api.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.api.schemas.base import SuccessResponse
from app.api.schemas.user import UserResponse
from app.core.containers import (
    get_login_use_case,
    get_logout_use_case,
    get_refresh_use_case,
    get_register_use_case,
)
from app.core.dependencies import get_token_payload
from app.core.exceptions import AuthenticationError, ConflictError

router = APIRouter(prefix="/auth", tags=["auth"])


def _request_meta(request: Request) -> tuple[str, str, str]:
    """Extract (request_id, ip, user_agent) from the request."""
    request_id = request.headers.get("X-Request-ID", "")
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "")
    return request_id, ip, user_agent


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: RegisterRequest,
    request: Request,
    uc=Depends(get_register_use_case),
) -> UserResponse:
    request_id, ip, ua = _request_meta(request)
    try:
        user = await uc.execute(
            dto=RegisterDTO(
                email=body.email,
                password=body.password,
                full_name=body.full_name,
            ),
            request_id=request_id,
            ip_address=ip,
            user_agent=ua,
        )
    except ValueError as exc:
        raise ConflictError(str(exc)) from exc

    return _map_user(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    uc=Depends(get_login_use_case),
) -> TokenResponse:
    request_id, ip, ua = _request_meta(request)
    try:
        tokens = await uc.execute(
            dto=LoginDTO(
                email=body.email,
                password=body.password,
                ip_address=ip,
                user_agent=ua,
                request_id=request_id,
            )
        )
    except PermissionError as exc:
        raise AuthenticationError(str(exc)) from exc
    except ValueError as exc:
        raise AuthenticationError("Invalid credentials") from exc

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    request: Request,
    uc=Depends(get_refresh_use_case),
) -> TokenResponse:
    request_id, ip, ua = _request_meta(request)
    try:
        tokens = await uc.execute(
            dto=RefreshDTO(
                refresh_token=body.refresh_token,
                ip_address=ip,
                user_agent=ua,
                request_id=request_id,
            )
        )
    except ValueError as exc:
        raise AuthenticationError(str(exc)) from exc

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
    )


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    request: Request,
    payload: dict = Depends(get_token_payload),
    uc=Depends(get_logout_use_case),
) -> SuccessResponse:
    request_id, ip, ua = _request_meta(request)
    auth_header = request.headers.get("Authorization", "")
    raw_access_token = auth_header.removeprefix("Bearer ").strip()

    refresh_token = (await request.json()).get("refresh_token", "") if request.headers.get("content-type") else ""

    await uc.execute(
        dto=LogoutDTO(
            access_token=raw_access_token,
            refresh_token=refresh_token,
            user_id=payload["sub"],
        ),
        request_id=request_id,
        ip_address=ip,
        user_agent=ua,
    )
    return SuccessResponse(message="Logged out successfully")


# ── local mapper ───────────────────────────────────────────────────────────

def _map_user(user) -> UserResponse:
    from app.api.schemas.user import RoleResponse, PermissionResponse
    return UserResponse(
        id=user.id,
        email=str(user.email),
        full_name=user.full_name,
        status=user.status.value,
        is_deleted=user.is_deleted,
        roles=[
            RoleResponse(
                id=r.id,
                name=r.name,
                description=r.description,
                is_active=r.is_active,
                permissions=[
                    PermissionResponse(
                        id=p.id,
                        codename=p.codename,
                        resource=p.resource,
                        action=p.action,
                        description=p.description,
                    )
                    for p in r.permissions
                ],
            )
            for r in user.roles
        ],
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
