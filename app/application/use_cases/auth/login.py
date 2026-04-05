from __future__ import annotations

from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.value_objects.email import Email
from app.domain.enums.action_type import ActionType
from app.core.token_service import AbstractTokenService
from app.core.cache_service import AbstractCacheService
from app.application.use_cases.auth.dtos import LoginDTO, TokenDTO


class LoginUseCase:
    """
    Authenticate a user and issue JWT tokens.

    - Brute force protection via cache (5 attempts / 15 min window)
    - Verifies email + password via domain value objects only
    - Token issuance + refresh token storage delegated to TokenService
    - TokenService handles all infrastructure concerns internally
    - Use case never touches DB models, sessions, or token hashes
    - Audit logged atomically in same UoW transaction
    """

    MAX_ATTEMPTS = 5
    LOCKOUT_SECONDS = 900  # 15 minutes

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        token_service: AbstractTokenService,
        cache: AbstractCacheService,
    ) -> None:
        self._uow = uow
        self._token_service = token_service
        self._cache = cache

    async def execute(self, dto: LoginDTO) -> TokenDTO:
        lock_key = f"login_attempts:{dto.email}"

        async with self._uow as uow:
            # 1. brute force check
            await self._check_brute_force(lock_key)

            # 2. fetch user by email
            email = Email(dto.email)
            user = await uow.users.get_by_email(email)

            if not user or not user.is_active:
                await self._record_failed_attempt(
                    lock_key=lock_key,
                    dto=dto,
                    uow=uow,
                    reason="user not found or inactive",
                )
                raise ValueError("Invalid credentials")

            # 3. reload with roles + permissions eagerly loaded
            user = await uow.users.get_by_id_with_roles(user.id)

            # 4. verify password — domain value object, zero infrastructure
            if not user.password.verify(dto.password):
                await self._record_failed_attempt(
                    lock_key=lock_key,
                    dto=dto,
                    uow=uow,
                    reason="invalid password",
                    actor_id=user.id,
                    actor_email=str(user.email),
                    actor_roles=user.get_role_names(),
                )
                raise ValueError("Invalid credentials")

            # 5. clear brute force counter on success
            await self._cache.delete(lock_key)

            # 6. issue tokens — TokenService handles all storage internally
            access_token = self._token_service.create_access_token(
                user_id=str(user.id),
                roles=user.get_role_names(),
                permissions=list(user.get_all_permissions()),
            )
            refresh_token = await self._token_service.create_and_store_refresh_token(
                user_id=user.id,
            )

            # 7. audit — atomic with the rest of the transaction
            audit = AuditLog.create_success(
                actor_id=user.id,
                actor_email=str(user.email),
                actor_roles=user.get_role_names(),
                action=ActionType.AUTH_LOGIN,
                resource="auth",
                request_id=dto.request_id,
                ip_address=dto.ip_address,
                user_agent=dto.user_agent,
                after={"status": "success"},
            )
            await uow.audit.log(audit)
            await uow.commit()

        return TokenDTO(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    # ── private helpers ────────────────────────────────────────────────────

    async def _check_brute_force(self, lock_key: str) -> None:
        raw = await self._cache.get(lock_key)
        if raw and int(raw) >= self.MAX_ATTEMPTS:
            raise PermissionError(
                "Too many failed login attempts. "
                "Account locked for 15 minutes."
            )

    async def _record_failed_attempt(
        self,
        lock_key: str,
        dto: LoginDTO,
        uow: AbstractUnitOfWork,
        reason: str,
        actor_id=None,
        actor_email: str = "unknown",
        actor_roles: list[str] | None = None,
    ) -> None:
        import uuid

        await self._cache.incr(lock_key)
        await self._cache.expire(lock_key, self.LOCKOUT_SECONDS)

        audit = AuditLog.create_failure(
            actor_id=actor_id or uuid.uuid4(),
            actor_email=actor_email,
            actor_roles=actor_roles or [],
            action=ActionType.AUTH_LOGIN_FAILED,
            resource="auth",
            request_id=dto.request_id,
            ip_address=dto.ip_address,
            user_agent=dto.user_agent,
            failure_reason=reason,
        )
        await uow.audit.log(audit)