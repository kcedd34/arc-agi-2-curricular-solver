"""HF Trainer callback enforcing the per-task neural time ceiling (ADR
0049 circuit breaker) during TTT, so an unusually slow per-task fine-tune
cannot by itself exhaust the ceiling before generation even starts.
"""
from transformers import TrainerCallback

from src.evaluation.task_time_limit import TaskTimeLimiter


class DeadlineTrainerCallback(TrainerCallback):
    def __init__(self, limiter: TaskTimeLimiter):
        self._limiter = limiter

    def on_step_end(self, args, state, control, **kwargs):
        self._limiter.check()
        return control
