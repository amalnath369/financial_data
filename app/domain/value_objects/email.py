from __future__ import annotations
import re


class Email:
    """
    Value object representing a validated, normalized email address.
    - Lowercased and stripped
    - Format validated
    - Immutable
    - Comparable by value
    """

    _PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    )
    MAX_LENGTH = 254  

    def __init__(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("Email must be a string")

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError("Email cannot be empty")

        if len(normalized) > self.MAX_LENGTH:
            raise ValueError(
                f"Email cannot exceed {self.MAX_LENGTH} characters"
            )

        if not self._PATTERN.match(normalized):
            raise ValueError(f"Invalid email format: {value!r}")

        self._value = normalized

    @property
    def value(self) -> str:
        return self._value

    @property
    def domain(self) -> str:
        return self._value.split("@")[1]

    @property
    def local_part(self) -> str:
        return self._value.split("@")[0]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Email):
            return NotImplemented
        return self._value == other._value

    def __repr__(self) -> str:
        return f"Email({self._value!r})"

    def __str__(self) -> str:
        return self._value

    def __hash__(self) -> int:
        return hash(self._value)