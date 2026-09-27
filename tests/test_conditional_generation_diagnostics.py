from src.evaluation.conditional_generation_diagnostics import generate_with_conditional_counts
from src.solvers.neural.config import NeuralSolverConfig

_CLEAN_GRID_TEXT = "12\n34"
_ANOTHER_CLEAN_GRID_TEXT = "56\n78"
_REPETITIVE_TEXT = "12\n" + "\n".join(["6666666666666"] * 12)
# Same width on every line (unlike _REPETITIVE_TEXT), so text_to_grid parses
# it as one rectangular grid; also 12 consecutive identical lines, matching
# ADR 0053/0055's 136b0064 misleading-parse pattern (ADR 0056).
_DEGENERATE_BUT_PARSEABLE_TEXT = "\n".join(["00"] * 12)


def _fake_completion_fn(completions_by_seed):
    def generate_completion(config, seed):
        return completions_by_seed[seed]
    return generate_completion


def test_no_escalation_when_first_attempt_is_clean():
    # Two distinct clean grids, so 2 predictions are kept and the loop stops
    # early without ever running out of scripted attempts.
    completions = {0: _CLEAN_GRID_TEXT, 1: _ANOTHER_CLEAN_GRID_TEXT}
    baseline = NeuralSolverConfig(num_predictions=2)
    diag = generate_with_conditional_counts(_fake_completion_fn(completions), baseline)
    assert diag.escalated is False
    assert diag.num_kept == 2


def test_escalates_after_a_degenerate_first_attempt():
    completions = {0: _REPETITIVE_TEXT, 1: _CLEAN_GRID_TEXT, 2: _ANOTHER_CLEAN_GRID_TEXT}
    baseline = NeuralSolverConfig(num_predictions=2)
    seen_configs = []

    def generate_completion(config, seed):
        seen_configs.append(config.no_repeat_ngram_size)
        return completions[seed]

    diag = generate_with_conditional_counts(generate_completion, baseline)
    assert diag.escalated is True
    # Attempt 0 used the baseline config (no_repeat_ngram_size=0); every
    # attempt after the degenerate first one switched to the escalated value.
    assert seen_configs[0] == 0
    assert all(size == 3 for size in seen_configs[1:])


def test_disabling_conditional_escalation_never_switches_config():
    completions = {0: _REPETITIVE_TEXT, 1: _REPETITIVE_TEXT, 2: _CLEAN_GRID_TEXT, 3: _ANOTHER_CLEAN_GRID_TEXT}
    baseline = NeuralSolverConfig(num_predictions=2)
    seen_configs = []

    def generate_completion(config, seed):
        seen_configs.append(config.no_repeat_ngram_size)
        return completions[seed]

    diag = generate_with_conditional_counts(generate_completion, baseline, enable_conditional_escalation=False)
    assert diag.escalated is False
    assert all(size == 0 for size in seen_configs)


def test_stops_early_once_enough_predictions_are_kept():
    completions = {0: _CLEAN_GRID_TEXT, 1: _ANOTHER_CLEAN_GRID_TEXT}
    baseline = NeuralSolverConfig(num_predictions=2)
    diag = generate_with_conditional_counts(_fake_completion_fn(completions), baseline)
    assert diag.attempts_tried == 2
    assert diag.num_kept == 2


def test_degenerate_but_parseable_completion_is_parsed_but_not_kept():
    # ADR 0056: a completion can be structurally parseable (consistent row
    # width) while its content is degenerate repetition. It must count
    # toward num_parsed but never become a kept prediction.
    completions = {0: _DEGENERATE_BUT_PARSEABLE_TEXT, 1: _CLEAN_GRID_TEXT, 2: _ANOTHER_CLEAN_GRID_TEXT}
    baseline = NeuralSolverConfig(num_predictions=2)
    diag = generate_with_conditional_counts(_fake_completion_fn(completions), baseline)
    assert diag.num_parsed == 3
    assert diag.num_parsed_but_degenerate == 1
    assert diag.num_kept == 2
    degenerate_grid = [[0, 0]] * 12
    assert degenerate_grid not in diag.predictions


def test_escalated_config_uses_a_custom_ngram_size():
    completions = {0: _REPETITIVE_TEXT, 1: _CLEAN_GRID_TEXT, 2: _ANOTHER_CLEAN_GRID_TEXT}
    baseline = NeuralSolverConfig(num_predictions=2)
    seen_configs = []

    def generate_completion(config, seed):
        seen_configs.append(config.no_repeat_ngram_size)
        return completions[seed]

    generate_with_conditional_counts(generate_completion, baseline, escalated_no_repeat_ngram_size=5)
    assert seen_configs[1:] == [5] * (len(seen_configs) - 1)
