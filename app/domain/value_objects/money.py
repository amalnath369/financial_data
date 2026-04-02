from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


class Money:
    """
    Value object representing a monetary amount.
    - Always positive
    - Max 2 decimal places
    - Max limit enforced
    - Immutable
    - Comparable and addable
    """

    MAX_AMOUNT = Decimal("999999999.99")
    MIN_AMOUNT = Decimal("0.01")
    QUANTIZE_EXP = Decimal("0.01")

    def __init__(self, amount: Decimal | int | float | str) -> None:
        try:
            value = Decimal(str(amount))
        except InvalidOperation:
            raise ValueError(f"Invalid monetary amount: {amount}")

        value = value.quantize(self.QUANTIZE_EXP, rounding=ROUND_HALF_UP)

        if value < self.MIN_AMOUNT:
            raise ValueError(
                f"Amount must be at least {self.MIN_AMOUNT}. Got: {value}"
            )

        if value > self.MAX_AMOUNT:
            raise ValueError(
                f"Amount cannot exceed {self.MAX_AMOUNT}. Got: {value}"
            )

        self._amount = value

    @property
    def amount(self) -> Decimal:
        return self._amount

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self._amount == other._amount

    def __lt__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self._amount < other._amount

    def __le__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self._amount <= other._amount

    def __gt__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self._amount > other._amount

    def __ge__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self._amount >= other._amount

    def __add__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self._amount + other._amount)

    def __sub__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        result = self._amount - other._amount
        if result < 0:
            raise ValueError("Money subtraction cannot result in negative value")
        return Money(result)

    def __repr__(self) -> str:
        return f"Money({self._amount})"

    def __str__(self) -> str:
        return str(self._amount)

    def __hash__(self) -> int:
        return hash(self._amount)

    def to_decimal(self) -> Decimal:
        return self._amount

    def to_float(self) -> float:
        return float(self._amount)

    @classmethod
    def zero(cls) -> Money:
        """Returns Money(0.00) — useful for aggregation starting points."""
        # bypass min check for zero
        instance = object.__new__(cls)
        instance._amount = Decimal("0.00")
        return instance

    @classmethod
    def from_decimal(cls, value: Decimal) -> Money:
        return cls(value)