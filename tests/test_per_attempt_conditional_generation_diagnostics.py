import pytest

from src.evaluation.per_attempt_conditional_generation_diagnostics import (
    generate_with_per_attempt_conditional_counts,
)
from src.evaluation.task_time_limit import TaskTimeExceeded, TaskTimeLimiter
from src.solvers.neural.config import NeuralSolverConfig

_CLEAN_GRID_TEXT = "12\n34"
_ANOTHER_CLEAN_GRID_TEXT = "56\n78"
_REPETITIVE_TEXT = "12\n" + "\n".join(["6666666666666"] * 12)
# Unparseable (not all-digit lines) but must also stay under has_topic_drift's
# 4-alphabetic-word natural-language threshold (ADR 0056), or this stops being
# a genuine false negative and gets caught by the new detector instead.
_UNPARSEABLE_NON_DEGENERATE_TEXT = "nonsense output"
# Same width on every line (unlike _REPETITIVE_TEXT), so text_to_grid parses
# it as one rectangular grid; also 12 consecutive identical lines, matching
# ADR 0053/0055's 136b0064 misleading-parse pattern (ADR 0056).
_DEGENERATE_BUT_PARSEABLE_TEXT = "\n".join(["00"] * 12)


def _fake_completion_fn(completions_by_seed):
    def generate_completion(config, seed):
        return completions_by_seed[seed]
    return generate_completion


def test_no_escalation_when_every_attempt_is_clean():
    completions = {0: _CLEAN_GRID_TEXT, 1: _ANOTHER_CLEAN_GRID_TEXT}
    baseline = NeuralSolverConfig(num_predictions=2)
    diag = generate_with_per_attempt_conditional_counts(_fake_completion_fn(completions), baseline)
    assert diag.escalated is False
    assert diag.escalated_at_attempt is None
    assert diag.num_kept == 2


def test_escalates_after_a_degenerate_first_attempt():
    completions = {0: _REPETITIVE_TEXT, 1: _CLEAN_GRID_TEXT, 2: _ANOTHER_CLEAN_GRID_TEXT}
    baseline = NeuralSolverConfig(num_predictions=2)
    seen_configs = []

    def generate_completion(config, seed):
        seen_configs.append(config.no_repeat_ngram_size)
        return completions[seed]

    diag = generate_with_per_attempt_conditional_counts(generate_completion, baseline)
    assert diag.escalated is True
    assert diag.escalated_at_attempt == 0
    assert seen_configs[0] == 0
    assert all(size == 3 for size in seen_configs[1:])


def test_recovers_when_first_attempt_is_a_false_negative():
    # Attempt 0 is a non-degenerate, unparseable false negative (the ADR
    # 0031 weakness): a first-attempt-only check would never escalate this
    # pair. Attempt 1 shows the pattern, so this per-attempt version should
    # still escalate for attempt 2 onward.
    completions = {
        0: _UNPARSEABLE_NON_DEGENERATE_TEXT,
        1: _REPETITIVE_TEXT,
        2: _CLEAN_GRID_TEXT,
        3: _ANOTHER_CLEAN_GRID_TEXT,
    }
    baseline = NeuralSolverConfig(num_predictions=2)
    seen_configs = []

    def generate_completion(config, seed):
        seen_configs.append(config.no_repeat_ngram_size)
        return completions[seed]

    diag = generate_with_per_attempt_conditional_counts(generate_completion, baseline)
    assert diag.escalated is True
    assert diag.escalated_at_attempt == 1
    # Attempts 0 and 1 both ran under baseline (attempt 1's own completion
    # is what reveals the pattern); every attempt after that is escalated.
    assert seen_configs[0] == 0
    assert seen_configs[1] == 0
    assert all(size == 3 for size in seen_configs[2:])


def test_disabling_conditional_escalation_never_switches_config():
    completions = {0: _REPETITIVE_TEXT, 1: _REPETITIVE_TEXT, 2: _CLEAN_GRID_TEXT, 3: _ANOTHER_CLEAN_GRID_TEXT}
    baseline = NeuralSolverConfig(num_predictions=2)
    seen_configs = []

    def generate_completion(config, seed):
        seen_configs.append(config.no_repeat_ngram_size)
        return completions[seed]

    diag = generate_with_per_attempt_conditional_counts(generate_completion, baseline, enable_conditional_escalation=False)
    assert diag.escalated is False
    assert diag.escalated_at_attempt is None
    assert all(size == 0 for size in seen_configs)


def test_stops_early_once_enough_predictions_are_kept():
    completions = {0: _CLEAN_GRID_TEXT, 1: _ANOTHER_CLEAN_GRID_TEXT}
    baseline = NeuralSolverConfig(num_predictions=2)
    diag = generate_with_per_attempt_conditional_counts(_fake_completion_fn(completions), baseline)
    assert diag.attempts_tried == 2
    assert diag.num_kept == 2


def test_escalation_stays_on_once_triggered_even_if_later_attempts_look_clean():
    completions = {
        0: _REPETITIVE_TEXT,
        1: _REPETITIVE_TEXT,
        2: _CLEAN_GRID_TEXT,
        3: _ANOTHER_CLEAN_GRID_TEXT,
    }
    baseline = NeuralSolverConfig(num_predictions=2)
    seen_configs = []

    def generate_completion(config, seed):
        seen_configs.append(config.no_repeat_ngram_size)
        return completions[seed]

    diag = generate_with_per_attempt_conditional_counts(generate_completion, baseline)
    assert diag.escalated_at_attempt == 0
    # No de-escalation: attempt 1's own repetitive text is checked, but the
    # policy was already escalated, so it stays escalated, not re-triggered.
    assert seen_configs[1:] == [3, 3, 3]


def test_degenerate_but_parseable_completion_is_parsed_but_not_kept():
    # ADR 0056: a completion can be structurally parseable (consistent row
    # width) while its content is degenerate repetition. It must count
    # toward num_parsed but never become a kept prediction.
    completions = {0: _DEGENERATE_BUT_PARSEABLE_TEXT, 1: _CLEAN_GRID_TEXT, 2: _ANOTHER_CLEAN_GRID_TEXT}
    baseline = NeuralSolverConfig(num_predictions=2)
    diag = generate_with_per_attempt_conditional_counts(_fake_completion_fn(completions), baseline)
    assert diag.num_parsed == 3
    assert diag.num_parsed_but_degenerate == 1
    assert diag.num_kept == 2
    degenerate_grid = [[0, 0]] * 12
    assert degenerate_grid not in diag.predictions


def _fake_clock(fake_time):
    return lambda: fake_time[0]


def test_limiter_check_runs_once_per_attempt_when_within_ceiling():
    completions = {0: _CLEAN_GRID_TEXT, 1: _ANOTHER_CLEAN_GRID_TEXT}
    baseline = NeuralSolverConfig(num_predictions=2)
    fake_time = [0.0]
    limiter = TaskTimeLimiter(ceiling_seconds=400.0, clock=_fake_clock(fake_time))
    limiter.start()

    diag = generate_with_per_attempt_conditional_counts(
        _fake_completion_fn(completions), baseline, limiter=limiter
    )
    assert diag.num_kept == 2


def test_limiter_exceeded_propagates_and_stops_further_attempts():
    # Attempt 0 checks the limiter while still within the ceiling; the fake
    # clock only jumps past it before attempt 1's check, so attempt 1 must
    # never call generate_completion at all (ADR 0058: mirrors
    # generation.py's production generate_grid_predictions loop, where the
    # check happens before the rest of the loop body runs).
    fake_time = [0.0]
    limiter = TaskTimeLimiter(ceiling_seconds=400.0, clock=_fake_clock(fake_time))
    limiter.start()
    calls = []

    def generate_completion(config, seed):
        calls.append(seed)
        fake_time[0] = 500.0
        return _CLEAN_GRID_TEXT

    baseline = NeuralSolverConfig(num_predictions=2)
    with pytest.raises(TaskTimeExceeded):
        generate_with_per_attempt_conditional_counts(generate_completion, baseline, limiter=limiter)
    assert calls == [0]


def test_escalated_config_uses_a_custom_ngram_size():
    completions = {0: _REPETITIVE_TEXT, 1: _CLEAN_GRID_TEXT, 2: _ANOTHER_CLEAN_GRID_TEXT}
    baseline = NeuralSolverConfig(num_predictions=2)
    seen_configs = []

    def generate_completion(config, seed):
        seen_configs.append(config.no_repeat_ngram_size)
        return completions[seed]

    generate_with_per_attempt_conditional_counts(generate_completion, baseline, escalated_no_repeat_ngram_size=5)
    assert seen_configs[1:] == [5] * (len(seen_configs) - 1)
