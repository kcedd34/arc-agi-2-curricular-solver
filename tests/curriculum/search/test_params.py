"""Unit tests for features.py/params.py on a tiny synthetic task (no GPU/disk needed)."""
from src.curriculum.loader import Task, TrainPair
from src.curriculum.search.features import colors_by_frequency, input_color_counts
from src.curriculum.search.params import candidates_for_param, candidates_for_primitive

_TASK = Task(
    task_id="synthetic",
    train=[
        TrainPair(input=[[0, 0, 1], [0, 0, 0]], output=[[1]]),
        TrainPair(input=[[0, 2, 2]], output=[[2]]),
    ],
    test_inputs=[[[0, 0]]],
)


def test_input_color_counts():
    counts = input_color_counts(_TASK)
    assert counts[0] == 6
    assert counts[1] == 1
    assert counts[2] == 2


def test_colors_by_frequency_most_common_first():
    assert colors_by_frequency(_TASK)[0] == 0


def test_candidates_for_param_background_is_hard_pruned_to_colors_common_to_every_input():
    """Round-1 pruning package (docs/curriculum/rounds/round-1.md):
    `background` is a detection role (draw_lines/isolated_point), hard-
    pruned to colors present in *every* train-pair input, not just the
    union of colors observed anywhere. On `_TASK`, pair 1's input has
    {0, 1} and pair 2's has {0, 2}: only 0 is common to both."""
    candidates = candidates_for_param("background", _TASK)
    assert set(candidates) == {0}


def test_candidates_for_param_fill_color_is_hard_pruned_to_added_colors():
    """`fill_color` is a write role (fill_content), hard-pruned to colors
    the train outputs actually add relative to their inputs."""
    candidates = candidates_for_param("fill_color", _TASK)
    assert set(candidates) == {1, 2}


def test_candidates_for_param_unknown_falls_back_to_all_colors():
    assert candidates_for_param("nonexistent_param", _TASK) == list(range(10))


def test_candidates_for_primitive_maps_every_param():
    result = candidates_for_primitive(["background"], _TASK)
    assert set(result.keys()) == {"background"}
    assert result["background"][0] == 0


def test_candidates_for_param_stop_condition_enumerates_all_three():
    """Task 4 (ADR 0068): SegmentTo's stop_condition is not prunable from
    the train pairs the way background/scale are, so all 3 values are
    always offered as search candidates."""
    candidates = candidates_for_param("stop_condition", _TASK)
    assert set(candidates) == {"same_color_isolated", "border", "any_obstacle"}
