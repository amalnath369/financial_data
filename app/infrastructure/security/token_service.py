from __future__ import annotations
import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.core.cache_service import AbstractCacheService
from app.core.config import Settings
from app.core.token_service import AbstractTokenService
from app.infrastructure.database.models.refresh_tokens import RefreshTokenModel
from app.infrastructure.database.models.roles import RoleModel
from app.infrastructure.database.models.role_permission import RolePermissionModel
from app.infrastructure.database.models.user_role import UserRoleModel
from app.infrastructure.database.models.users import UserModel
from app.infrastructure.repositories.mappers import map_user


class JWTTokenService(AbstractTokenService):
    """
    JWT-based implementation of AbstractTokenService.

    Access tokens
    ─────────────
    · HS256-signed JWTs carrying sub, roles, permissions, jti, exp
    · On logout the JTI is written to the cache with TTL = remaining seconds
    · decode_access_token checks the blacklist before returning the payload

    Refresh tokens
    ──────────────
    · HS256-signed JWTs carrying sub, jti, exp
    · The SHA-256 hash of the raw JWT is stored in refresh_tokens table
    · Rotation: old record marked revoked → new token created in same tx
    · On logout: token hash looked up and marked revoked

    This class owns its own DB sessions for token storage so it stays
    decoupled from the Unit-of-Work used by business use cases.
    """

    _BLACKLIST_PREFIX = "blacklist:jti:"

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        cache: AbstractCacheService,
        settings: Settings,
    ) -> None:
        self._session_factory = session_factory
        self._cache = cache
        self._secret = settings.JWT_SECRET_KEY
        self._algorithm = settings.JWT_ALGORITHM
        self._access_ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self._refresh_ttl_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    # ── access tokens ──────────────────────────────────────────────────────

    def create_access_token(
        self,
        user_id: str,
        roles: list[str],
        permissions: list[str],
    ) -> str:
        now = datetime.now(tz=timezone.utc)
        payload = {
            "sub": user_id,
            "roles": roles,
            "permissions": permissions,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": now + timedelta(minutes=self._access_ttl),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    async def decode_access_token(self, raw_token: str) -> dict:
        """
        Validate signature + expiry, then check the JTI blacklist.
        Raises ValueError for bad tokens, PermissionError if blacklisted.
        """
        try:
            payload = jwt.decode(
                raw_token, self._secret, algorithms=[self._algorithm]
            )
        except JWTError as exc:
            raise ValueError(f"Invalid access token: {exc}") from exc

        jti = payload.get("jti")
        if not jti:
            raise ValueError("Access token is missing jti claim")

        blacklisted = await self._cache.get(f"{self._BLACKLIST_PREFIX}{jti}")
        if blacklisted:
            raise PermissionError("Access token has been revoked")

        return payload

    async def blacklist_access_token(self, raw_access_token: str) -> None:
        """
        Store the JTI in cache with TTL = remaining token lifetime.
        No-op if the token is already expired or malformed.
        """
        try:
            payload = jwt.decode(
                raw_access_token, self._secret, algorithms=[self._algorithm]
            )
        except JWTError:
            return  # nothing to blacklist

        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or not exp:
            return

        remaining = int(exp) - int(datetime.now(tz=timezone.utc).timestamp())
        if remaining > 0:
            await self._cache.set(
                f"{self._BLACKLIST_PREFIX}{jti}",
                "1",
                remaining,
            )

    # ── refresh tokens ─────────────────────────────────────────────────────

    async def create_and_store_refresh_token(self, user_id: uuid.UUID) -> str:
        """
        Issue a refresh JWT, hash it, persist the hash, return raw token.
        """
        now = datetime.now(tz=timezone.utc)
        expires_at = now + timedelta(days=self._refresh_ttl_days)

        payload = {
            "sub": str(user_id),
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": expires_at,
        }
        raw_token: str = jwt.encode(
            payload, self._secret, algorithm=self._algorithm
        )

        async with self._session_factory() as session:
            session.add(RefreshTokenModel(
                id=uuid.uuid4(),
                user_id=user_id,
                token_hash=self._hash(raw_token),
                expires_at=expires_at,
                revoked=False,
            ))
            await session.commit()

        return raw_token

    def decode_refresh_token(self, raw_token: str) -> dict:
        """
        Validate signature and expiry only — no DB or cache access.
        Revocation is enforced inside rotate_refresh_token via DB lookup.
        """
        try:
            return jwt.decode(
                raw_token, self._secret, algorithms=[self._algorithm]
            )
        except JWTError as exc:
            raise ValueError(f"Invalid refresh token: {exc}") from exc

    async def rotate_refresh_token(
        self, raw_refresh_token: str
    ) -> tuple[str, str]:
        """
        Atomic refresh-token rotation in a single DB transaction:
          1. Verify the old token exists in DB and is not revoked / expired
          2. Mark old record as revoked
          3. Load the user's current roles + permissions (always fresh)
          4. Issue new access token + new refresh token
          5. Persist new refresh token hash
        """
        # Validate JWT signature / expiry before touching the DB
        payload = self.decode_refresh_token(raw_refresh_token)
        user_id = uuid.UUID(payload["sub"])
        old_hash = self._hash(raw_refresh_token)

        async with self._session_factory() as session:
            # 1. fetch and validate the stored token record
            result = await session.execute(
                select(RefreshTokenModel).where(
                    RefreshTokenModel.token_hash == old_hash,
                    RefreshTokenModel.user_id == user_id,
                )
            )
            record = result.scalar_one_or_none()

            if not record:
                raise ValueError("Refresh token not found")
            if record.revoked:
                raise ValueError("Refresh token has already been revoked")
            if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(
                tz=timezone.utc
            ):
                raise ValueError("Refresh token has expired")

            # 2. revoke old record
            record.revoked = True

            # 3. load user with current roles + permissions
            user_result = await session.execute(
                select(UserModel)
                .options(
                    selectinload(UserModel.user_roles)
                    .selectinload(UserRoleModel.role)
                    .selectinload(RoleModel.role_permissions)
                    .selectinload(RolePermissionModel.permission)
                )
                .where(
                    UserModel.id == user_id,
                    UserModel.is_deleted == False,  # noqa: E712
                )
            )
            user_model = user_result.scalar_one_or_none()
            if not user_model:
                raise ValueError("User not found or deleted")

            user = map_user(user_model)

            # 4. issue new access token (uses fresh roles/permissions)
            new_access_token = self.create_access_token(
                user_id=str(user.id),
                roles=user.get_role_names(),
                permissions=list(user.get_all_permissions()),
            )

            # 5. create and persist new refresh token
            now = datetime.now(tz=timezone.utc)
            expires_at = now + timedelta(days=self._refresh_ttl_days)
            new_payload = {
                "sub": str(user_id),
                "jti": str(uuid.uuid4()),
                "iat": now,
                "exp": expires_at,
            }
            new_raw_token: str = jwt.encode(
                new_payload, self._secret, algorithm=self._algorithm
            )
            session.add(RefreshTokenModel(
                id=uuid.uuid4(),
                user_id=user_id,
                token_hash=self._hash(new_raw_token),
                expires_at=expires_at,
                revoked=False,
            ))

            await session.commit()

        return new_access_token, new_raw_token

    async def revoke_refresh_token(
        self,
        user_id: uuid.UUID,
        raw_refresh_token: str,
    ) -> None:
        """
        Mark a refresh token as revoked on logout.
        No-op if token not found (already expired and cleaned up).
        """
        token_hash = self._hash(raw_refresh_token)

        async with self._session_factory() as session:
            result = await session.execute(
                select(RefreshTokenModel).where(
                    RefreshTokenModel.token_hash == token_hash,
                    RefreshTokenModel.user_id == user_id,
                )
            )
            record = result.scalar_one_or_none()
            if record and not record.revoked:
                record.revoked = True
                await session.commit()

    # ── private ────────────────────────────────────────────────────────────

    @staticmethod
    def _hash(raw_token: str) -> str:
        """SHA-256 hex digest — safe to store, cannot reverse to raw token."""
        return hashlib.sha256(raw_token.encode()).hexdigest()
