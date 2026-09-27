from src.solvers.neural import generation
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.generation import _truncate_before_second_input, generate_grid_predictions

_CLEAN_GRID_TEXT = "12\n34"
_ANOTHER_CLEAN_GRID_TEXT = "56\n78"
# Same width on every line, so text_to_grid parses it as one rectangular
# grid; also 12 consecutive identical lines, matching the ADR 0053/0055
# 136b0064 misleading-parse pattern (ADR 0056).
_DEGENERATE_BUT_PARSEABLE_TEXT = "\n".join(["00"] * 12)


def test_leaves_a_clean_completion_untouched():
    completion = "123\n456\n789"
    assert _truncate_before_second_input(completion) == completion


def test_truncates_at_the_first_second_input_marker():
    completion = "123\n456\n789\n\nOutput:\n123\n\nInput:\n999\n888\n\nOutput:\n111"
    assert _truncate_before_second_input(completion) == "123\n456\n789\n\nOutput:\n123\n"


def test_truncates_at_the_earliest_marker_when_more_than_one():
    completion = "12\n\nInput:\nfirst\n\nInput:\nsecond"
    assert _truncate_before_second_input(completion) == "12\n"


def _patch_completions(monkeypatch, completions_by_seed):
    def fake_generate_completion(model, tokenizer, prompt, config, seed, limiter=None):
        return completions_by_seed[seed]

    monkeypatch.setattr(generation, "_generate_completion", fake_generate_completion)


def test_degenerate_completion_is_never_kept_as_a_prediction(monkeypatch):
    # ADR 0056: a degenerate-but-parseable completion (e.g. an all-zero grid
    # repeated past the detection threshold) must never reach predictions,
    # even though text_to_grid successfully parses it into a grid.
    completions = {0: _DEGENERATE_BUT_PARSEABLE_TEXT, 1: _CLEAN_GRID_TEXT, 2: _ANOTHER_CLEAN_GRID_TEXT}
    _patch_completions(monkeypatch, completions)
    config = NeuralSolverConfig(num_predictions=2)
    predictions = generate_grid_predictions(None, None, [[0]], config)
    assert predictions == [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]
    degenerate_grid = [[0, 0]] * 12
    assert degenerate_grid not in predictions
