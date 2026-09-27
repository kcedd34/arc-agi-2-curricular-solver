"""Per-task wall-clock ceiling for neural processing (ADR 0049 circuit
breaker). Distinct from time_budget.py's TimeBudget, which only gates
whether the *next* task's neural attempt starts; this limiter aborts a
single task's own TTT+generation mid-flight once it runs away, so one
anomalous task (see the still-undiagnosed 264363fd outlier) cannot by
itself consume a large, unpredictable share of the shared neural-pass
budget.
"""
import time
from dataclasses import dataclass, field
from typing import Callable, List

NEURAL_TASK_CEILING_SECONDS = 400.0


class TaskTimeExceeded(Exception):
    """Raised when a single task's neural processing exceeds its ceiling."""


@dataclass
class TaskTimeLimiter:
    ceiling_seconds: float
    clock: Callable[[], float] = time.monotonic
    _start: float = field(default=0.0, init=False, repr=False)

    def start(self) -> None:
        self._start = self.clock()

    def elapsed(self) -> float:
        return self.clock() - self._start

    def deadline(self) -> float:
        return self._start + self.ceiling_seconds

    def check(self) -> None:
        elapsed = self.elapsed()
        if elapsed > self.ceiling_seconds:
            raise TaskTimeExceeded(
                f"neural processing exceeded the {self.ceiling_seconds:.0f}s "
                f"per-task ceiling ({elapsed:.1f}s elapsed)"
            )


@dataclass
class TimeLimitAbortTracker:
    """Records which tasks were aborted by the per-task time ceiling, so a
    real 240-task run can report how often this triggers in practice."""
    aborted_task_ids: List[str] = field(default_factory=list)

    def record_abort(self, task_id: str) -> None:
        self.aborted_task_ids.append(task_id)

    @property
    def count(self) -> int:
        return len(self.aborted_task_ids)
