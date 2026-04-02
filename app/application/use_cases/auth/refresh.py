from __future__ import annotations
import uuid

from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.enums.action_type import ActionType
from app.core.token_service import AbstractTokenService
from app.application.use_cases.auth.dtos import RefreshDTO, TokenDTO


class RefreshTokenUseCase:
    """
    Rotate JWT tokens.

    - Token validation + revocation + new token storage
      all delegated to TokenService (infrastructure concern)
    - Use case only orchestrates: validate user still active,
      call token_service.rotate(), audit the event
    - Zero infrastructure imports
    """

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        token_service: AbstractTokenService,
    ) -> None:
        self._uow = uow
        self._token_service = token_service

    async def execute(self, dto: RefreshDTO) -> TokenDTO:
        # 1. decode to get user_id — token_service validates signature
        payload = self._token_service.decode_refresh_token(dto.refresh_token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise ValueError("Invalid refresh token")

        user_id = uuid.UUID(user_id_str)

        async with self._uow as uow:
            # 2. confirm user still active
            user = await uow.users.get_by_id_with_roles(user_id)
            if not user or not user.is_active:
                raise ValueError("User not found or inactive")

            # 3. rotate tokens — validation + revocation + storage all internal
            access_token, new_refresh_token = (
                await self._token_service.rotate_refresh_token(
                    raw_refresh_token=dto.refresh_token,
                )
            )

            # 4. audit
            audit = AuditLog.create_success(
                actor_id=user.id,
                actor_email=str(user.email),
                actor_roles=user.get_role_names(),
                action=ActionType.AUTH_TOKEN_REFRESH,
                resource="auth",
                request_id=dto.ip_address,
                ip_address=dto.ip_address,
                user_agent=dto.user_agent,
            )
            await uow.audit.log(audit)
            await uow.commit()

        return TokenDTO(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )