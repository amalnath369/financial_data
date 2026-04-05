from __future__ import annotations
from typing import Callable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.token_service import AbstractTokenService

_bearer = HTTPBearer(auto_error=False)


async def get_token_payload(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """
    Extract and validate the Bearer token from the Authorization header.
    Returns the decoded JWT payload dict.
    Raises AuthenticationError if missing or invalid.
    """
    if not credentials:
        raise AuthenticationError("Bearer token required")

    token_service: AbstractTokenService = request.app.state.token_service

    try:
        payload = await token_service.decode_access_token(credentials.credentials)
    except PermissionError as exc:
        raise AuthenticationError(str(exc)) from exc
    except ValueError as exc:
        raise AuthenticationError(str(exc)) from exc

    return payload


def get_current_user_id(
    payload: dict = Depends(get_token_payload),
) -> str:
    """Return the user_id (sub) from the token payload."""
    return payload["sub"]


def get_current_roles(
    payload: dict = Depends(get_token_payload),
) -> list[str]:
    return payload.get("roles", [])


def get_current_permissions(
    payload: dict = Depends(get_token_payload),
) -> list[str]:
    return payload.get("permissions", [])


def require_permission(codename: str) -> Callable:
    """
    FastAPI dependency factory.

    Usage:
        @router.get("/admin")
        async def admin(
            _: None = Depends(require_permission("users:read"))
        ): ...
    """
    async def _check(
        permissions: list[str] = Depends(get_current_permissions),
    ) -> None:
        if codename not in permissions:
            raise AuthorizationError(
                f"Permission '{codename}' required"
            )

    return _check
