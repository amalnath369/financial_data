from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, categories, dashboard, health, records, roles, users

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(records.router)
api_router.include_router(categories.router)
api_router.include_router(roles.router)
api_router.include_router(dashboard.router)
