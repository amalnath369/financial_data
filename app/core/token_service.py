from __future__ import annotations
from abc import ABC, abstractmethod
import uuid


class AbstractTokenService(ABC):
    """
    Token service interface — lives in core layer.

    Use cases depend on this interface only.
    The concrete implementation lives in infrastructure
    and handles all refresh token DB storage internally.

    This keeps all JWT + token storage concerns
    completely out of the domain and use case layers.
    """

    @abstractmethod
    def create_access_token(
        self,
        user_id: str,
        roles: list[str],
        permissions: list[str],
    ) -> str:
        """Issue a signed JWT access token (15 min TTL)."""
        raise NotImplementedError

    @abstractmethod
    async def create_and_store_refresh_token(
        self,
        user_id: uuid.UUID,
    ) -> str:
        """
        Issue a refresh token, hash it, store in DB, return raw token.
        All storage handled internally — caller never sees the hash or DB record.
        """
        raise NotImplementedError

    @abstractmethod
    async def rotate_refresh_token(
        self,
        raw_refresh_token: str,
    ) -> tuple[str, str]:
        """
        Validate old refresh token, revoke it, issue new pair.
        Returns (new_access_token, new_refresh_token).
        Raises ValueError if token invalid, expired, or already revoked.
        """
        raise NotImplementedError

    @abstractmethod
    async def revoke_refresh_token(
        self,
        user_id: uuid.UUID,
        raw_refresh_token: str,
    ) -> None:
        """
        Revoke a specific refresh token on logout.
        No-op if token not found.
        """
        raise NotImplementedError

    @abstractmethod
    async def blacklist_access_token(
        self,
        raw_access_token: str,
    ) -> None:
        """
        Blacklist access token JTI in Redis with TTL = remaining expiry.
        Degrades gracefully if Redis is unavailable.
        """
        raise NotImplementedError

    @abstractmethod
    def decode_access_token(self, raw_token: str) -> dict:
        """
        Decode and validate an access token.
        Raises ValueError if invalid or expired.
        Raises PermissionError if JTI is blacklisted.
        """
        raise NotImplementedError

    @abstractmethod
    def decode_refresh_token(self, raw_token: str) -> dict:
        """
        Decode and validate a refresh token.
        Raises ValueError if invalid or expired.
        """
        raise NotImplementedError