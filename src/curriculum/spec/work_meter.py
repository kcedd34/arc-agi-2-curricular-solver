"""Deterministic work meter for bounded searches (ADR 0101).

The primary limit is a count of work units (interpreter runs weighted by
input grid cells), so two executions explore
exactly the same space. The wall-clock deadline is only a safety net for
pathological cases; when it cuts, `tripped` is "deadline" and callers must
report it. Independent of `library/` (RN-CUR-14)."""
import time
from contextlib import contextmanager
from typing import Iterator, Optional

WORK = "work"
DEADLINE = "deadline"


class WorkBudgetExceeded(BaseException):
    """BaseException so generic `except Exception` handlers in searches do
    not swallow it; only the metered stage catches it."""


class _Meter:
    def __init__(self) -> None:
        self.active = False
        self.units = 0
        self.unit_limit: Optional[int] = None
        self.end: Optional[float] = None
        self.tripped: Optional[str] = None


_METER = _Meter()


def charge(units: int = 1) -> None:
    if not _METER.active:
        return
    _METER.units += units
    if _METER.unit_limit is not None and _METER.units > _METER.unit_limit:
        _METER.tripped = WORK
        raise WorkBudgetExceeded(WORK)
    if _METER.end is not None and time.monotonic() >= _METER.end:
        _METER.tripped = DEADLINE
        raise WorkBudgetExceeded(DEADLINE)


def tripped() -> Optional[str]:
    return _METER.tripped


def units_used() -> int:
    return _METER.units


@contextmanager
def metered(unit_limit: Optional[int], deadline_seconds: Optional[float]) -> Iterator[None]:
    previous = (_METER.active, _METER.units, _METER.unit_limit, _METER.end, _METER.tripped)
    _METER.active, _METER.units, _METER.tripped = True, 0, None
    _METER.unit_limit = unit_limit
    _METER.end = None if deadline_seconds is None else time.monotonic() + deadline_seconds
    try:
        yield
    finally:
        _METER.active, _METER.units, _METER.unit_limit, _METER.end, _METER.tripped = previous
