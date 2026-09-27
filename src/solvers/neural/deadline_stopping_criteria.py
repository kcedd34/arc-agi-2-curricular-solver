"""Stops a single model.generate() call once a wall-clock deadline passes
(ADR 0049 circuit breaker), so one slow completion cannot by itself blow
through the per-task time ceiling regardless of max_new_tokens.
"""
import time
from typing import Callable

from transformers import StoppingCriteria


class DeadlineStoppingCriteria(StoppingCriteria):
    def __init__(self, deadline: float, clock: Callable[[], float] = time.monotonic):
        self._deadline = deadline
        self._clock = clock

    def __call__(self, input_ids, scores, **kwargs) -> bool:
        return self._clock() >= self._deadline
