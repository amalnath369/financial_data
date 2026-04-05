from __future__ import annotations

from fastapi import Request

from app.core.cache_service import AbstractCacheService
from app.core.config import settings
from app.core.token_service import AbstractTokenService
from app.domain.repositories.uow import AbstractUnitOfWork
from app.infrastructure.database.session import AsyncSessionFactory
from app.infrastructure.database.uow import SQLAlchemyUnitOfWork
from app.infrastructure.redis.cache_service import RedisCacheService
from app.infrastructure.redis.redis import get_redis
from app.infrastructure.security.token_service import JWTTokenService

# ── use-case imports ───────────────────────────────────────────────────────
from app.application.use_cases.auth.login import LoginUseCase
from app.application.use_cases.auth.logout import LogoutUseCase
from app.application.use_cases.auth.refresh import RefreshTokenUseCase
from app.application.use_cases.auth.register import RegisterUseCase

from app.application.use_cases.users.create_user import CreateUserUseCase
from app.application.use_cases.users.get_user import GetUserUseCase, GetUsersUseCase
from app.application.use_cases.users.update_user import UpdateUserUseCase
from app.application.use_cases.users.delete_user import DeleteUserUseCase
from app.application.use_cases.users.change_status import ChangeUserStatusUseCase
from app.application.use_cases.users.manage_roles import (
    AssignRoleToUserUseCase,
    RemoveRoleFromUserUseCase,
)

from app.application.use_cases.records.create_record import CreateRecordUseCase
from app.application.use_cases.records.get_record import GetRecordUseCase, GetRecordsUseCase
from app.application.use_cases.records.update_record import UpdateRecordUseCase
from app.application.use_cases.records.delete_record import DeleteRecordUseCase

from app.application.use_cases.categories.create_category import CreateCategoryUseCase
from app.application.use_cases.categories.get_categorys import GetCategoriesUseCase, GetCategoryUseCase
from app.application.use_cases.categories.update_category import UpdateCategoryUseCase
from app.application.use_cases.categories.delete_category import DeleteCategoryUseCase

from app.application.use_cases.roles.create import CreateRoleUseCase
from app.application.use_cases.roles.get import GetRolesUseCase, GetRoleUseCase
from app.application.use_cases.roles.update import UpdateRoleUseCase
from app.application.use_cases.roles.delete import DeleteRoleUseCase
from app.application.use_cases.roles.manage_permissions import (
    AssignPermissionsToRoleUseCase,
    RemovePermissionsFromRoleUseCase,
)

from app.application.use_cases.dashboard.get_summary import GetDashboardSummaryUseCase
from app.application.use_cases.dashboard.get_category_totals import GetCategoryTotalsUseCase
from app.application.use_cases.dashboard.get_trends import GetTrendsUseCase
from app.application.use_cases.dashboard.get_recents import GetRecentActivityUseCase


async def build_cache() -> AbstractCacheService:
    """Build the shared RedisCacheService from the global Redis client."""
    redis_client = await get_redis()
    return RedisCacheService(redis_client)


async def build_token_service(cache: AbstractCacheService) -> AbstractTokenService:
    return JWTTokenService(
        session_factory=AsyncSessionFactory,
        cache=cache,
        settings=settings,
    )


def build_uow(cache: AbstractCacheService) -> AbstractUnitOfWork:
    return SQLAlchemyUnitOfWork(
        session_factory=AsyncSessionFactory,
        cache=cache,
    )


# ── FastAPI dependency helpers ─────────────────────────────────────────────
# Each function reads the singletons stored on app.state and builds
# a fresh use-case instance (use cases are lightweight, stateless).

def _cache(request: Request) -> AbstractCacheService:
    return request.app.state.cache


def _uow(request: Request) -> AbstractUnitOfWork:
    return build_uow(request.app.state.cache)


def _token_service(request: Request) -> AbstractTokenService:
    return request.app.state.token_service


# ── Auth ───────────────────────────────────────────────────────────────────

def get_login_use_case(request: Request) -> LoginUseCase:
    return LoginUseCase(uow=_uow(request), token_service=_token_service(request), cache=_cache(request))


def get_logout_use_case(request: Request) -> LogoutUseCase:
    return LogoutUseCase(uow=_uow(request), token_service=_token_service(request))


def get_refresh_use_case(request: Request) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(uow=_uow(request), token_service=_token_service(request))


def get_register_use_case(request: Request) -> RegisterUseCase:
    return RegisterUseCase(uow=_uow(request))


# ── Users ──────────────────────────────────────────────────────────────────

def get_create_user_uc(request: Request) -> CreateUserUseCase:
    return CreateUserUseCase(uow=_uow(request))


def get_get_user_uc(request: Request) -> GetUserUseCase:
    return GetUserUseCase(uow=_uow(request))


def get_get_users_uc(request: Request) -> GetUsersUseCase:
    return GetUsersUseCase(uow=_uow(request))


def get_update_user_uc(request: Request) -> UpdateUserUseCase:
    return UpdateUserUseCase(uow=_uow(request))


def get_delete_user_uc(request: Request) -> DeleteUserUseCase:
    return DeleteUserUseCase(uow=_uow(request))


def get_change_status_uc(request: Request) -> ChangeUserStatusUseCase:
    return ChangeUserStatusUseCase(uow=_uow(request))


def get_assign_role_uc(request: Request) -> AssignRoleToUserUseCase:
    return AssignRoleToUserUseCase(uow=_uow(request))


def get_remove_role_uc(request: Request) -> RemoveRoleFromUserUseCase:
    return RemoveRoleFromUserUseCase(uow=_uow(request))


# ── Records ────────────────────────────────────────────────────────────────

def get_create_record_uc(request: Request) -> CreateRecordUseCase:
    return CreateRecordUseCase(uow=_uow(request), cache=_cache(request))


def get_get_record_uc(request: Request) -> GetRecordUseCase:
    return GetRecordUseCase(uow=_uow(request))


def get_get_records_uc(request: Request) -> GetRecordsUseCase:
    return GetRecordsUseCase(uow=_uow(request))


def get_update_record_uc(request: Request) -> UpdateRecordUseCase:
    return UpdateRecordUseCase(uow=_uow(request), cache=_cache(request))


def get_delete_record_uc(request: Request) -> DeleteRecordUseCase:
    return DeleteRecordUseCase(uow=_uow(request), cache=_cache(request))


# ── Categories ─────────────────────────────────────────────────────────────

def get_create_category_uc(request: Request) -> CreateCategoryUseCase:
    return CreateCategoryUseCase(uow=_uow(request))


def get_get_categories_uc(request: Request) -> GetCategoriesUseCase:
    return GetCategoriesUseCase(uow=_uow(request))


def get_get_category_uc(request: Request) -> GetCategoryUseCase:
    return GetCategoryUseCase(uow=_uow(request))


def get_update_category_uc(request: Request) -> UpdateCategoryUseCase:
    return UpdateCategoryUseCase(uow=_uow(request))


def get_delete_category_uc(request: Request) -> DeleteCategoryUseCase:
    return DeleteCategoryUseCase(uow=_uow(request))


# ── Roles ──────────────────────────────────────────────────────────────────

def get_create_role_uc(request: Request) -> CreateRoleUseCase:
    return CreateRoleUseCase(uow=_uow(request))


def get_get_roles_uc(request: Request) -> GetRolesUseCase:
    return GetRolesUseCase(uow=_uow(request))


def get_get_role_uc(request: Request) -> GetRoleUseCase:
    return GetRoleUseCase(uow=_uow(request))


def get_update_role_uc(request: Request) -> UpdateRoleUseCase:
    return UpdateRoleUseCase(uow=_uow(request))


def get_delete_role_uc(request: Request) -> DeleteRoleUseCase:
    return DeleteRoleUseCase(uow=_uow(request))


def get_assign_perms_uc(request: Request) -> AssignPermissionsToRoleUseCase:
    return AssignPermissionsToRoleUseCase(uow=_uow(request))


def get_remove_perms_uc(request: Request) -> RemovePermissionsFromRoleUseCase:
    return RemovePermissionsFromRoleUseCase(uow=_uow(request))


# ── Dashboard ──────────────────────────────────────────────────────────────

def get_summary_uc(request: Request) -> GetDashboardSummaryUseCase:
    return GetDashboardSummaryUseCase(uow=_uow(request), cache=_cache(request))


def get_category_totals_uc(request: Request) -> GetCategoryTotalsUseCase:
    return GetCategoryTotalsUseCase(uow=_uow(request), cache=_cache(request))


def get_trends_uc(request: Request) -> GetTrendsUseCase:
    return GetTrendsUseCase(uow=_uow(request), cache=_cache(request))


def get_recents_uc(request: Request) -> GetRecentActivityUseCase:
    return GetRecentActivityUseCase(uow=_uow(request))
