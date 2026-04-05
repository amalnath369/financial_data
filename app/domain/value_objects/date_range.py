from __future__ import annotations
from datetime import date


class DateRange:
    """
    Value object representing a validated date range.
    - Start must be before or equal to end
    - End cannot be in the future
    - Immutable
    - Usable in both record filtering and dashboard trends
    """

    def __init__(self, start: date, end: date) -> None:
        if not isinstance(start, date):
            raise ValueError("Start must be a date instance")

        if not isinstance(end, date):
            raise ValueError("End must be a date instance")

        if start > end:
            raise ValueError(
                f"Start date {start} cannot be after end date {end}"
            )

        today = date.today()
        if end > today:
            raise ValueError(
                f"End date {end} cannot be in the future (today is {today})"
            )

        self._start = start
        self._end = end

    @property
    def start(self) -> date:
        return self._start

    @property
    def end(self) -> date:
        return self._end

    @property
    def days(self) -> int:
        """Number of days in the range (inclusive)."""
        return (self._end - self._start).days + 1

    def contains(self, d: date) -> bool:
        """Returns True if the given date falls within this range."""
        return self._start <= d <= self._end

    def overlaps(self, other: DateRange) -> bool:
        """Returns True if this range overlaps with another."""
        return self._start <= other._end and self._end >= other._start

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DateRange):
            return NotImplemented
        return self._start == other._start and self._end == other._end

    def __repr__(self) -> str:
        return f"DateRange({self._start} → {self._end}, {self.days} days)"

    def __hash__(self) -> int:
        return hash((self._start, self._end))

    @classmethod
    def last_n_days(cls, n: int) -> DateRange:
        """Convenience factory — last N days up to today."""
        from datetime import timedelta
        end = date.today()
        start = end - timedelta(days=n - 1)
        return cls(start, end)

    @classmethod
    def current_month(cls) -> DateRange:
        """Convenience factory — first day of current month to today."""
        today = date.today()
        return cls(date(today.year, today.month, 1), today)

    @classmethod
    def current_week(cls) -> DateRange:
        """Convenience factory — Monday to today of current week."""
        today = date.today()
        start = today - __import__("datetime").timedelta(days=today.weekday())
        return cls(start, today)