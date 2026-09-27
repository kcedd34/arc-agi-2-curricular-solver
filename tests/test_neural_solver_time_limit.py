"""Integration-level tests for the ADR 0049 per-task time circuit breaker
in src/solvers/neural_solver.py. These simulate an artificially slow task
by advancing a fake clock inside fake train_on_task/generate_grid_predictions
stand-ins, mirroring the fake-neural_solve pattern already used in
tests/test_build_hybrid_submission.py, so no real GPU/model is required.

Type shapes, spelled out to avoid nesting mistakes:
- Grid = List[List[int]], e.g. GRID_TWO = [[2]] is a 1x1 grid holding 2.
- generate_grid_predictions/baseline_predict return List[Grid] (a
  candidate list), e.g. [GRID_TWO].
- solve_task returns List[List[Grid]], one candidate list per test pair,
  e.g. [[GRID_TWO]].
"""
import pytest

pytest.importorskip("unsloth")

from src.evaluation.task_time_limit import TaskTimeLimiter  # noqa: E402
from src.solvers import neural_solver  # noqa: E402
from src.utils.task_loader import Pair, Task  # noqa: E402

TRAIN_INPUT = [[1]]
TRAIN_OUTPUT = [[2]]
TEST_INPUT = [[3]]
TEST_OUTPUT = [[4]]
FALLBACK_GRID = [[9]]

_TASK = Task(
    task_id="fake-task",
    train=[Pair(input=TRAIN_INPUT, output=TRAIN_OUTPUT)],
    test=[Pair(input=TEST_INPUT, output=TEST_OUTPUT)],
)

_EXPECTED_FALLBACK_RESULT = [[FALLBACK_GRID]]
_EXPECTED_NEURAL_RESULT = [[TEST_OUTPUT]]


def _fake_clock(fake_time):
    return lambda: fake_time[0]


def _patch_common(monkeypatch, fake_time):
    monkeypatch.setattr(
        neural_solver,
        "TaskTimeLimiter",
        lambda ceiling_seconds: TaskTimeLimiter(ceiling_seconds=ceiling_seconds, clock=_fake_clock(fake_time)),
    )
    monkeypatch.setattr(neural_solver, "_get_base_model", lambda: (object(), object()))
    monkeypatch.setattr(neural_solver, "attach_fresh_lora", lambda base_model, config: base_model)
    monkeypatch.setattr(neural_solver, "detach_lora", lambda model: model)
    monkeypatch.setattr(neural_solver, "baseline_predict", lambda task, grid: [FALLBACK_GRID])
    neural_solver.TIME_LIMIT_ABORTS.aborted_task_ids.clear()


def test_slow_task_is_aborted_and_falls_back_to_baseline(monkeypatch):
    fake_time = [0.0]

    def slow_train_on_task(model, tokenizer, task, config, limiter=None):
        fake_time[0] = neural_solver.NEURAL_TASK_CEILING_SECONDS + 1.0
        limiter.check()
        return model

    _patch_common(monkeypatch, fake_time)
    monkeypatch.setattr(neural_solver, "train_on_task", slow_train_on_task)
    monkeypatch.setattr(
        neural_solver,
        "generate_grid_predictions",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not be reached, task should abort in TTT")),
    )

    result = neural_solver.solve_task(_TASK)

    assert result == _EXPECTED_FALLBACK_RESULT
    assert neural_solver.TIME_LIMIT_ABORTS.count == 1
    assert neural_solver.TIME_LIMIT_ABORTS.aborted_task_ids == ["fake-task"]


def test_normal_speed_task_is_not_aborted(monkeypatch):
    fake_time = [0.0]

    def fast_train_on_task(model, tokenizer, task, config, limiter=None):
        fake_time[0] = 5.0
        return model

    def fast_generate_grid_predictions(model, tokenizer, test_input, config, limiter=None):
        fake_time[0] += 1.0
        return [TRAIN_OUTPUT] if test_input == TRAIN_INPUT else [TEST_OUTPUT]

    _patch_common(monkeypatch, fake_time)
    monkeypatch.setattr(neural_solver, "train_on_task", fast_train_on_task)
    monkeypatch.setattr(neural_solver, "generate_grid_predictions", fast_generate_grid_predictions)

    result = neural_solver.solve_task(_TASK)

    assert result == _EXPECTED_NEURAL_RESULT
    assert neural_solver.TIME_LIMIT_ABORTS.count == 0


def test_slow_generation_after_fast_ttt_is_also_aborted(monkeypatch):
    fake_time = [0.0]
    call_count = [0]

    def fast_train_on_task(model, tokenizer, task, config, limiter=None):
        fake_time[0] = 5.0
        return model

    def slow_generate_grid_predictions(model, tokenizer, test_input, config, limiter=None):
        call_count[0] += 1
        fake_time[0] = neural_solver.NEURAL_TASK_CEILING_SECONDS + 1.0
        limiter.check()
        return [TRAIN_OUTPUT]

    _patch_common(monkeypatch, fake_time)
    monkeypatch.setattr(neural_solver, "train_on_task", fast_train_on_task)
    monkeypatch.setattr(neural_solver, "generate_grid_predictions", slow_generate_grid_predictions)

    result = neural_solver.solve_task(_TASK)

    assert result == _EXPECTED_FALLBACK_RESULT
    assert neural_solver.TIME_LIMIT_ABORTS.count == 1
    assert call_count[0] == 1
