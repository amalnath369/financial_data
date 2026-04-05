from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import AppError


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Maps every AppError subclass to its HTTP status + detail."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected exceptions — returns 500 without leaking internals."""
    import structlog
    log = structlog.get_logger()
    log.exception("unhandled_error", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"},
    )


async def pydantic_error_handler(
    request: Request, exc: PydanticValidationError
) -> JSONResponse:
    """Converts Pydantic v2 validation errors into a readable 422 response."""
    errors = [
        {"loc": list(e["loc"]), "msg": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})
