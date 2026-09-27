"""Tracks a wall-clock ceiling for the neural pass of the hybrid pipeline
(ADR 0049), so it can be stopped early and remaining tasks kept on their
symbolic fallback answer instead of risking the Kaggle 12h limit.
"""
import time
from dataclasses import dataclass, field
from typing import Callable

TOTAL_KAGGLE_BUDGET_SECONDS = 12 * 3600
SAFETY_MARGIN_SECONDS = 4 * 3600
NEURAL_PASS_CEILING_SECONDS = TOTAL_KAGGLE_BUDGET_SECONDS - SAFETY_MARGIN_SECONDS


@dataclass
class TimeBudget:
    ceiling_seconds: float
    clock: Callable[[], float] = time.monotonic
    _elapsed_seconds: float = field(default=0.0, init=False, repr=False)

    def record(self, seconds: float) -> None:
        self._elapsed_seconds += max(seconds, 0.0)

    def is_exhausted(self) -> bool:
        return self._elapsed_seconds >= self.ceiling_seconds

    def remaining_seconds(self) -> float:
        return max(self.ceiling_seconds - self._elapsed_seconds, 0.0)

    def elapsed_seconds(self) -> float:
        return self._elapsed_seconds
