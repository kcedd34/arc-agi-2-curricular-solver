from src.evaluation import generation_diagnostics
from src.solvers.neural.config import NeuralSolverConfig

_CLEAN_GRID_TEXT = "12\n34"
_ANOTHER_CLEAN_GRID_TEXT = "56\n78"
# Same width on every line, so text_to_grid parses it as one rectangular
# grid; also 12 consecutive identical lines, matching ADR 0053/0055's
# 136b0064 misleading-parse pattern (ADR 0056).
_DEGENERATE_BUT_PARSEABLE_TEXT = "\n".join(["00"] * 12)
_UNPARSEABLE_TEXT = "not a grid at all"


def _patch_completions(monkeypatch, completions_by_seed):
    def fake_generate_completion(model, tokenizer, prompt, config, seed):
        return completions_by_seed[seed]

    monkeypatch.setattr(generation_diagnostics, "_generate_completion", fake_generate_completion)


def test_two_clean_completions_are_both_kept(monkeypatch):
    _patch_completions(monkeypatch, {0: _CLEAN_GRID_TEXT, 1: _ANOTHER_CLEAN_GRID_TEXT})
    config = NeuralSolverConfig(num_predictions=2)
    diag = generation_diagnostics.generate_with_counts(None, None, [[0]], config)
    assert diag.attempts_tried == 2
    assert diag.num_parsed == 2
    assert diag.num_parsed_but_degenerate == 0
    assert diag.num_kept == 2


def test_unparseable_completion_is_not_counted_as_parsed(monkeypatch):
    completions = {0: _UNPARSEABLE_TEXT, 1: _CLEAN_GRID_TEXT, 2: _ANOTHER_CLEAN_GRID_TEXT}
    _patch_completions(monkeypatch, completions)
    config = NeuralSolverConfig(num_predictions=2)
    diag = generation_diagnostics.generate_with_counts(None, None, [[0]], config)
    assert diag.num_parsed == 2
    assert diag.num_kept == 2


def test_degenerate_but_parseable_completion_is_parsed_but_not_kept(monkeypatch):
    # ADR 0056: a completion can be structurally parseable (consistent row
    # width) while its content is degenerate repetition. It must count
    # toward num_parsed but never become a kept prediction.
    completions = {0: _DEGENERATE_BUT_PARSEABLE_TEXT, 1: _CLEAN_GRID_TEXT, 2: _ANOTHER_CLEAN_GRID_TEXT}
    _patch_completions(monkeypatch, completions)
    config = NeuralSolverConfig(num_predictions=2)
    diag = generation_diagnostics.generate_with_counts(None, None, [[0]], config)
    assert diag.num_parsed == 3
    assert diag.num_parsed_but_degenerate == 1
    assert diag.num_kept == 2
    degenerate_grid = [[0, 0]] * 12
    assert degenerate_grid not in diag.predictions


def test_stops_early_once_enough_predictions_are_kept(monkeypatch):
    _patch_completions(monkeypatch, {0: _CLEAN_GRID_TEXT, 1: _ANOTHER_CLEAN_GRID_TEXT})
    config = NeuralSolverConfig(num_predictions=2)
    diag = generation_diagnostics.generate_with_counts(None, None, [[0]], config)
    assert diag.attempts_tried == 2
