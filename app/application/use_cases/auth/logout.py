from __future__ import annotations
import uuid

from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.enums.action_type import ActionType
from app.core.token_service import AbstractTokenService
from app.application.use_cases.auth.dtos import LogoutDTO


class LogoutUseCase:
    """
    Logout a user.

    - Access token JTI blacklisted in Redis via TokenService
    - Refresh token revoked in DB via TokenService
    - All token operations delegated to TokenService (infra concern)
    - Use case only orchestrates: revoke tokens, audit the event
    - Zero infrastructure imports
    """

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        token_service: AbstractTokenService,
    ) -> None:
        self._uow = uow
        self._token_service = token_service

    async def execute(
        self,
        dto: LogoutDTO,
        ip_address: str,
        user_agent: str,
    ) -> None:
        user_id = uuid.UUID(dto.user_id)

        async with self._uow as uow:
            # 1. blacklist access token JTI in Redis — infra handled internally
            await self._token_service.blacklist_access_token(dto.access_token)

            # 2. revoke refresh token in DB — infra handled internally
            if dto.refresh_token:
                await self._token_service.revoke_refresh_token(
                    user_id=user_id,
                    raw_refresh_token=dto.refresh_token,
                )

            # 3. load user for audit snapshot
            user = await uow.users.get_by_id_with_roles(user_id)
            actor_email = str(user.email) if user else "unknown"
            actor_roles = user.get_role_names() if user else []

            # 4. audit
            audit = AuditLog.create_success(
                actor_id=user_id,
                actor_email=actor_email,
                actor_roles=actor_roles,
                action=ActionType.AUTH_LOGOUT,
                resource="auth",
                request_id=ip_address,
                ip_address=ip_address,
                user_agent=user_agent,
                after={"token_revoked": True},
            )
            await uow.audit.log(audit)
            await uow.commit()