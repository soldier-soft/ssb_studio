"""Clock abstraction allowing injectable monotonic time for testing and production."""

import time
from typing import Protocol


class Clock(Protocol):
    """Protocol for monotonic time sources."""

    def now(self) -> float:
        """Return the current monotonic timestamp in seconds."""
        ...


class SystemClock:
    """Production clock utilizing system monotonic time."""

    def now(self) -> float:
        return time.monotonic()


class TestClock:
    """Deterministic, manually advanceable clock for automated unit and timing tests."""
    __test__ = False

    def __init__(self, initial_time: float = 1000.0) -> None:
        self._current_time = float(initial_time)

    def now(self) -> float:
        return self._current_time

    def set_time(self, timestamp: float) -> None:
        self._current_time = float(timestamp)

    def advance(self, seconds: float) -> float:
        if seconds < 0:
            raise ValueError("TestClock cannot travel backwards in time")
        self._current_time += float(seconds)
        return self._current_time
