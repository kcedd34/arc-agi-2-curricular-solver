from src.solvers.object_heuristics import (
    ObjectHeuristic,
    apply_object_heuristic,
    detect_object_heuristics,
)
from src.utils.task_loader import Pair


def test_detects_largest_component_zero_background_4_connected():
    pairs = [
        Pair(
            input=[[0, 1, 1, 1], [0, 0, 0, 2], [0, 0, 0, 0]],
            output=[[1, 1, 1]],
        ),
        Pair(
            input=[[3, 3, 0], [0, 0, 0], [0, 5, 0]],
            output=[[3, 3]],
        ),
    ]
    hypotheses = detect_object_heuristics(pairs)
    assert ObjectHeuristic("zero", 4, "largest") in hypotheses


def test_detects_rarest_color_component():
    pairs = [
        Pair(
            input=[[1, 1, 1], [1, 1, 9], [1, 1, 1]],
            output=[[9]],
        ),
        Pair(
            input=[[2, 2, 2, 2], [2, 2, 2, 7]],
            output=[[7]],
        ),
    ]
    hypotheses = detect_object_heuristics(pairs)
    assert ObjectHeuristic("zero", 4, "rarest_color") in hypotheses


def test_no_candidate_when_output_is_not_any_component_bbox():
    pairs = [
        Pair(input=[[1, 0], [0, 0]], output=[[9, 9], [9, 9]]),
    ]
    assert detect_object_heuristics(pairs) == []


def test_ambiguous_when_multiple_variants_fit_a_single_object_grid():
    # A single non-background object with no other colors present: every
    # background/connectivity/selection combination reduces to the same
    # bounding box, so many variants "fit" - this is exactly the case the
    # caller must treat as ambiguous, not resolve arbitrarily.
    pairs = [
        Pair(input=[[0, 0], [0, 5]], output=[[5]]),
    ]
    hypotheses = detect_object_heuristics(pairs)
    assert len(hypotheses) > 1


def test_apply_object_heuristic_directly():
    heuristic = ObjectHeuristic("zero", 4, "largest")
    grid = [[0, 1, 1], [0, 0, 0], [2, 0, 0]]
    assert apply_object_heuristic(heuristic, grid) == [[1, 1]]
