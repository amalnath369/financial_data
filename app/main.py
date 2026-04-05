from __future__ import annotations

import structlog
import structlog.stdlib
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError as PydanticValidationError

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.containers import build_cache, build_token_service
from app.core.exceptions import AppError
from app.infrastructure.redis.redis import close_redis
from app.middleware.error_handler import (
    app_error_handler,
    pydantic_error_handler,
    unhandled_error_handler,
)
from app.middleware.logging import LoggingMiddleware
from app.middleware.request_id import RequestIDMiddleware


def _configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Build shared singletons on startup, tear them down on shutdown."""
    _configure_logging()

    cache = await build_cache()
    token_service = await build_token_service(cache)

    app.state.cache = cache
    app.state.token_service = token_service

    yield

    await close_redis()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Finance Data Processing API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── middleware (order: outermost first) ───────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],         
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # ── exception handlers ────────────────────────────────────────────────
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    # ── routes ────────────────────────────────────────────────────────────
    app.include_router(api_router)

    return app


app = create_app()
