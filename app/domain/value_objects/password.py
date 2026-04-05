from __future__ import annotations
import re
import hashlib
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Password:
    """
    Value object representing a hashed password.
    - Validates strength before hashing
    - Uses SHA-256 normalization to bypass bcrypt 72-byte limit
    - Stores only the hash, never the raw value
    - Provides verify() for authentication
    - Immutable
    """

    MIN_LENGTH = 8
    MAX_LENGTH = 128  # you can increase this now safely if needed

    def __init__(self, raw: str) -> None:
        if not isinstance(raw, str):
            raise ValueError("Password must be a string")

        self._validate_strength(raw)

        # 🔥 FIX: normalize password to fixed length (32 bytes)
        normalized = hashlib.sha256(raw.encode()).digest()

        # bcrypt hash (safe now)
        self._hashed = _pwd_context.hash(normalized)

    @classmethod
    def from_hash(cls, hashed: str) -> Password:
        """
        Reconstruct a Password value object from an already-hashed string.
        Used when loading from the database — skips validation and hashing.
        """
        instance = object.__new__(cls)
        instance._hashed = hashed
        return instance

    def verify(self, raw: str) -> bool:
        """Returns True if raw matches the stored hash."""
        normalized = hashlib.sha256(raw.encode()).digest()
        return _pwd_context.verify(normalized, self._hashed)

    def needs_rehash(self) -> bool:
        """Returns True if the hash algorithm is outdated and should be upgraded."""
        return _pwd_context.needs_update(self._hashed)

    @property
    def hashed(self) -> str:
        return self._hashed

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Password):
            return NotImplemented
        return self._hashed == other._hashed

    def __repr__(self) -> str:
        return "Password(***)"

    def __str__(self) -> str:
        return "***"

    def __hash__(self) -> int:
        return hash(self._hashed)

    @classmethod
    def _validate_strength(cls, raw: str) -> None:
        errors = []

        if len(raw) < cls.MIN_LENGTH:
            errors.append(f"at least {cls.MIN_LENGTH} characters")

        if len(raw) > cls.MAX_LENGTH:
            errors.append(f"no more than {cls.MAX_LENGTH} characters")

        if not re.search(r"[A-Z]", raw):
            errors.append("at least one uppercase letter")

        if not re.search(r"[a-z]", raw):
            errors.append("at least one lowercase letter")

        if not re.search(r"\d", raw):
            errors.append("at least one digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", raw):
            errors.append("at least one special character")

        if errors:
            raise ValueError(
                "Password must contain: " + ", ".join(errors)
            )