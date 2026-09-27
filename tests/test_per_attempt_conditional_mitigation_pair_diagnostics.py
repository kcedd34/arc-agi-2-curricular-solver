"""Tests for the ADR 0058 circuit breaker wiring in
src/evaluation/per_attempt_conditional_mitigation_pair_diagnostics.py.

Two tiers, mirroring the lazy-import boundary that module itself
documents (same boundary as ADR 0023):

- _diagnose_pair has no lazy imports of its own (_generate_completion and
  generate_with_per_attempt_conditional_counts are both module-level
  imports), so it is tested directly here with no unsloth dependency,
  monkeypatching per_attempt_conditional_mitigation_pair_diagnostics's own
  _generate_completion attribute.
- diagnose_task_with_per_attempt_conditional_mitigation lazily imports
  attach_fresh_lora/attach_pretrained_lora/detach_lora (from
  src.solvers.neural.lora_setup) and train_on_task (from
  src.solvers.neural.ttt_trainer) inside its own body, resolved from
  their source modules at call time. lora_setup imports unsloth at
  module level, so pytest.importorskip("unsloth") gates this whole
  file, and the fakes are installed on the source modules themselves
  (src.solvers.neural.lora_setup / src.solvers.neural.ttt_trainer), not
  on per_attempt_conditional_mitigation_pair_diagnostics, since that is
  where the lazy import actually resolves the names from.
"""
import pytest

pytest.importorskip("unsloth")

from src.evaluation import per_attempt_conditional_mitigation_pair_diagnostics as pair_diag  # noqa: E402
from src.evaluation.task_time_limit import TaskTimeExceeded, TaskTimeLimiter  # noqa: E402
from src.solvers.neural import lora_setup, ttt_trainer  # noqa: E402
from src.solvers.neural.config import NeuralSolverConfig  # noqa: E402
from src.utils.task_loader import Pair, Task  # noqa: E402

_CLEAN_GRID_TEXT = "12\n34"

_TASK = Task(
    task_id="fake-task",
    train=[Pair(input=[[1]], output=[[1, 2]])],
    test=[Pair(input=[[3]], output=[[3, 4]])],
)


def _fake_clock(fake_time):
    return lambda: fake_time[0]


def test_diagnose_pair_forwards_limiter_to_generate_completion(monkeypatch, tmp_path):
    seen_limiters = []

    def fake_generate_completion(model, tokenizer, prompt, config, seed, limiter):
        seen_limiters.append(limiter)
        return _CLEAN_GRID_TEXT

    monkeypatch.setattr(pair_diag, "_generate_completion", fake_generate_completion)

    # A real, working limiter, not a bare object(): the diagnostic loop
    # itself calls limiter.check() once per attempt (ADR 0058), on top of
    # forwarding the same instance into _generate_completion.
    sentinel_limiter = TaskTimeLimiter(ceiling_seconds=400.0, clock=_fake_clock([0.0]))
    sentinel_limiter.start()
    config = NeuralSolverConfig(num_predictions=1)
    row = pair_diag._diagnose_pair(
        model=object(), tokenizer=object(), config=config, config_name="cfg",
        task_id="fake-task", rule_holds=False, split="test", pair_index=0,
        pair=_TASK.test[0], raw_output_dir=tmp_path, enable_conditional_escalation=True,
        limiter=sentinel_limiter,
    )

    assert seen_limiters == [sentinel_limiter]
    assert row.num_kept == 1


def test_diagnose_pair_propagates_time_exceeded_from_generation(monkeypatch, tmp_path):
    fake_time = [0.0]
    limiter = TaskTimeLimiter(ceiling_seconds=400.0, clock=_fake_clock(fake_time))
    limiter.start()

    def fake_generate_completion(model, tokenizer, prompt, config, seed, limiter):
        fake_time[0] = 500.0
        return _CLEAN_GRID_TEXT

    monkeypatch.setattr(pair_diag, "_generate_completion", fake_generate_completion)

    config = NeuralSolverConfig(num_predictions=1)
    with pytest.raises(TaskTimeExceeded):
        pair_diag._diagnose_pair(
            model=object(), tokenizer=object(), config=config, config_name="cfg",
            task_id="fake-task", rule_holds=False, split="test", pair_index=0,
            pair=_TASK.test[0], raw_output_dir=tmp_path, enable_conditional_escalation=True,
            limiter=limiter,
        )


def _patch_lora(monkeypatch):
    monkeypatch.setattr(lora_setup, "attach_fresh_lora", lambda base_model, config: base_model)
    monkeypatch.setattr(lora_setup, "attach_pretrained_lora", lambda base_model, config, adapter_dir: base_model)
    detach_calls = []
    monkeypatch.setattr(lora_setup, "detach_lora", lambda model: detach_calls.append(model))
    return detach_calls


def test_diagnose_task_forwards_limiter_to_train_on_task_and_every_pair(monkeypatch, tmp_path):
    _patch_lora(monkeypatch)
    seen_limiters_train = []

    def fake_train_on_task(model, tokenizer, task, config, limiter=None):
        seen_limiters_train.append(limiter)
        return model

    monkeypatch.setattr(ttt_trainer, "train_on_task", fake_train_on_task)

    seen_limiters_generate = []

    def fake_generate_completion(model, tokenizer, prompt, config, seed, limiter):
        seen_limiters_generate.append(limiter)
        return _CLEAN_GRID_TEXT

    monkeypatch.setattr(pair_diag, "_generate_completion", fake_generate_completion)

    # A real, working limiter (see the note in the previous test): the
    # per-pair generation loop calls limiter.check() once per attempt.
    sentinel_limiter = TaskTimeLimiter(ceiling_seconds=400.0, clock=_fake_clock([0.0]))
    sentinel_limiter.start()
    config = NeuralSolverConfig(num_predictions=1)
    rows, timing = pair_diag.diagnose_task_with_per_attempt_conditional_mitigation(
        base_model=object(), tokenizer=object(), config=config, config_name="cfg",
        task=_TASK, raw_output_dir=tmp_path, limiter=sentinel_limiter,
    )

    assert seen_limiters_train == [sentinel_limiter]
    # One generate_completion call per pair (1 train + 1 test, num_predictions=1).
    assert seen_limiters_generate == [sentinel_limiter, sentinel_limiter]
    assert len(rows) == 2


def test_diagnose_task_time_exceeded_during_train_still_detaches(monkeypatch, tmp_path):
    detach_calls = _patch_lora(monkeypatch)

    def fake_train_on_task(model, tokenizer, task, config, limiter=None):
        raise TaskTimeExceeded("exceeded during training")

    monkeypatch.setattr(ttt_trainer, "train_on_task", fake_train_on_task)

    config = NeuralSolverConfig(num_predictions=1)
    with pytest.raises(TaskTimeExceeded):
        pair_diag.diagnose_task_with_per_attempt_conditional_mitigation(
            base_model=object(), tokenizer=object(), config=config, config_name="cfg",
            task=_TASK, raw_output_dir=tmp_path, limiter=object(),
        )
    # try/finally must still detach even though TaskTimeExceeded propagates
    # (ADR 0058: mirrors neural_solver.solve_task's abort-and-fall-back split).
    assert len(detach_calls) == 1


def test_diagnose_task_time_exceeded_during_generation_still_detaches(monkeypatch, tmp_path):
    detach_calls = _patch_lora(monkeypatch)

    def fake_train_on_task(model, tokenizer, task, config, limiter=None):
        return model

    monkeypatch.setattr(ttt_trainer, "train_on_task", fake_train_on_task)

    fake_time = [0.0]
    limiter = TaskTimeLimiter(ceiling_seconds=400.0, clock=_fake_clock(fake_time))
    limiter.start()

    def fake_generate_completion(model, tokenizer, prompt, config, seed, limiter):
        fake_time[0] = 500.0
        return _CLEAN_GRID_TEXT

    monkeypatch.setattr(pair_diag, "_generate_completion", fake_generate_completion)

    config = NeuralSolverConfig(num_predictions=1)
    with pytest.raises(TaskTimeExceeded):
        pair_diag.diagnose_task_with_per_attempt_conditional_mitigation(
            base_model=object(), tokenizer=object(), config=config, config_name="cfg",
            task=_TASK, raw_output_dir=tmp_path, limiter=limiter,
        )
    assert len(detach_calls) == 1
