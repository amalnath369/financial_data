from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    db: str
    cache: str


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    """Liveness — always returns 200 if the process is running."""
    return HealthResponse(status="ok", db="unknown", cache="unknown")


@router.get("/readiness", response_model=HealthResponse)
async def readiness(request: Request) -> HealthResponse:
    """
    Readiness — checks DB and Redis connectivity.
    Returns 503 if either dependency is down.
    """
    from fastapi import HTTPException
    from sqlalchemy import text

    db_status = "ok"
    cache_status = "ok"

    try:
        from app.infrastructure.database.session import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    try:
        cache = request.app.state.cache
        await cache.get("__readiness__")
    except Exception:
        cache_status = "error"

    if db_status != "ok" or cache_status != "ok":
        raise HTTPException(
            status_code=503,
            detail={"db": db_status, "cache": cache_status},
        )

    return HealthResponse(status="ok", db=db_status, cache=cache_status)
