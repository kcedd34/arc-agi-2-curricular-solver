"""Neural solver: Qwen3-4B-Instruct-2507 + LoRA/Unsloth + per-task TTT
(ADR 0003, base model replaced by ADR 0051), with the symbolic baseline as
a fallback layer (ADR 0001). Conforms to the same Solver interface used by
the evaluation harness and by src/solvers/baseline_solver.py.
"""
from typing import List, Optional

from src.evaluation.task_time_limit import (
    NEURAL_TASK_CEILING_SECONDS,
    TaskTimeExceeded,
    TaskTimeLimiter,
    TimeLimitAbortTracker,
)
from src.solvers.baseline_solver import predict_test_input as baseline_predict
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.generation import generate_grid_predictions
from src.solvers.neural.lora_setup import attach_fresh_lora, detach_lora
from src.solvers.neural.model_loader import load_base_model
from src.solvers.neural.ttt_trainer import train_on_task
from src.utils.grid_types import Grid
from src.utils.task_loader import Task

_CONFIG = NeuralSolverConfig()
_BASE_MODEL = None
_TOKENIZER = None

# ADR 0049 circuit breaker: counts tasks aborted by NEURAL_TASK_CEILING_SECONDS
# across a run, so real-run visibility into how common this is does not
# depend on reading logs after the fact.
TIME_LIMIT_ABORTS = TimeLimitAbortTracker()


def _get_base_model():
    global _BASE_MODEL, _TOKENIZER
    if _BASE_MODEL is None:
        _BASE_MODEL, _TOKENIZER = load_base_model(_CONFIG)
    return _BASE_MODEL, _TOKENIZER


def _passes_self_consistency(model, tokenizer, task: Task, limiter: TaskTimeLimiter) -> bool:
    for pair in task.train:
        limiter.check()
        predictions = generate_grid_predictions(model, tokenizer, pair.input, _CONFIG, limiter)
        if pair.output not in predictions:
            return False
    return True


def _predict_task_with_neural_solver(task: Task, limiter: TaskTimeLimiter) -> Optional[List[List[Grid]]]:
    base_model, tokenizer = _get_base_model()
    model = attach_fresh_lora(base_model, _CONFIG)
    try:
        model = train_on_task(model, tokenizer, task, _CONFIG, limiter=limiter)
        if not _passes_self_consistency(model, tokenizer, task, limiter):
            return None
        return [generate_grid_predictions(model, tokenizer, pair.input, _CONFIG, limiter) for pair in task.test]
    finally:
        detach_lora(model)


def solve_task(task: Task) -> List[List[Grid]]:
    """ADR 0049 circuit breaker: if this task's TTT+generation exceeds
    NEURAL_TASK_CEILING_SECONDS, neural processing is aborted for this task
    specifically (TIME_LIMIT_ABORTS records it) and the already-existing
    fallback chain applies, the symbolic baseline_predict per test pair,
    which itself defers to ADR 0011's safety net at the submission layer
    when it has no candidate either. This does not diagnose why a task ran
    long, it only bounds the damage.
    """
    limiter = TaskTimeLimiter(ceiling_seconds=NEURAL_TASK_CEILING_SECONDS)
    limiter.start()
    try:
        neural_predictions = _predict_task_with_neural_solver(task, limiter)
    except TaskTimeExceeded:
        TIME_LIMIT_ABORTS.record_abort(task.task_id)
        neural_predictions = None
    if neural_predictions is not None and all(neural_predictions):
        return neural_predictions
    return [baseline_predict(task, pair.input) for pair in task.test]
