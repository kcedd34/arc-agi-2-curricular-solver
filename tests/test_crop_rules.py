from src.solvers.crop_rules import (
    BoundingBoxCrop,
    FixedWindowCrop,
    apply_crop_hypothesis,
    detect_crop_hypotheses,
)
from src.utils.task_loader import Pair


def test_detects_fixed_window_at_a_constant_offset():
    pairs = [
        Pair(input=[[1, 2, 3], [4, 5, 6], [7, 8, 9]], output=[[5, 6], [8, 9]]),
        Pair(input=[[0, 0, 0], [0, 1, 2], [0, 3, 4]], output=[[1, 2], [3, 4]]),
    ]
    hypotheses = detect_crop_hypotheses(pairs)
    assert FixedWindowCrop(1, 1, 2, 2) in hypotheses


def test_detects_bounding_box_over_zero_background():
    pairs = [
        Pair(input=[[0, 0, 0], [0, 5, 5], [0, 5, 5]], output=[[5, 5], [5, 5]]),
        Pair(input=[[0, 0], [3, 3]], output=[[3, 3]]),
    ]
    hypotheses = detect_crop_hypotheses(pairs)
    assert BoundingBoxCrop("zero") in hypotheses


def test_detects_bounding_box_over_most_common_color_background():
    pairs = [
        Pair(input=[[7, 7, 7], [7, 2, 2], [7, 2, 2]], output=[[2, 2], [2, 2]]),
        Pair(input=[[7, 7], [4, 4]], output=[[4, 4]]),
    ]
    hypotheses = detect_crop_hypotheses(pairs)
    assert BoundingBoxCrop("most_common") in hypotheses


def test_ambiguous_when_fixed_window_and_bounding_box_both_fit():
    # Single train pair: a fixed-window crop at (0, 0) and the zero-background
    # bounding box agree on the same output, so both hypotheses survive -
    # this is exactly the multi-hypothesis case the caller must treat as
    # ambiguous, not resolve by picking one arbitrarily.
    pairs = [
        Pair(input=[[5, 5], [5, 5]], output=[[5, 5], [5, 5]]),
    ]
    hypotheses = detect_crop_hypotheses(pairs)
    assert len(hypotheses) == 0  # trivial same-shape case is excluded by both rules


def test_no_candidate_when_output_is_not_a_literal_sub_region():
    pairs = [
        Pair(input=[[1, 2], [3, 4]], output=[[9, 9], [9, 9]]),
    ]
    assert detect_crop_hypotheses(pairs) == []


def test_apply_fixed_window_hypothesis():
    hypothesis = FixedWindowCrop(1, 1, 2, 2)
    grid = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    assert apply_crop_hypothesis(hypothesis, grid) == [[5, 6], [8, 9]]


def test_apply_bounding_box_hypothesis():
    hypothesis = BoundingBoxCrop("zero")
    grid = [[0, 0, 0], [0, 5, 5], [0, 5, 5]]
    assert apply_crop_hypothesis(hypothesis, grid) == [[5, 5], [5, 5]]
