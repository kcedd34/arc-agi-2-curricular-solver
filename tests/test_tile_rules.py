from src.solvers.tile_rules import TileRepeat, apply_tile_hypothesis, detect_tile_hypotheses
from src.utils.task_loader import Pair


def test_detects_a_2x2_literal_repeat():
    pairs = [
        Pair(
            input=[[1, 2], [3, 4]],
            output=[[1, 2, 1, 2], [3, 4, 3, 4], [1, 2, 1, 2], [3, 4, 3, 4]],
        ),
        Pair(
            input=[[5, 6], [7, 8]],
            output=[[5, 6, 5, 6], [7, 8, 7, 8], [5, 6, 5, 6], [7, 8, 7, 8]],
        ),
    ]
    hypotheses = detect_tile_hypotheses(pairs)
    assert hypotheses == [TileRepeat(2, 2)]


def test_detects_a_1x3_literal_repeat():
    pairs = [
        Pair(input=[[1, 2]], output=[[1, 2, 1, 2, 1, 2]]),
    ]
    assert detect_tile_hypotheses(pairs) == [TileRepeat(1, 3)]


def test_no_candidate_when_repeat_factor_is_not_constant_across_pairs():
    pairs = [
        Pair(input=[[1]], output=[[1, 1]]),
        Pair(input=[[2]], output=[[2, 2, 2]]),
    ]
    assert detect_tile_hypotheses(pairs) == []


def test_no_candidate_when_output_shape_is_not_an_integer_multiple():
    pairs = [
        Pair(input=[[1, 2, 3]], output=[[1, 2, 3, 1]]),
    ]
    assert detect_tile_hypotheses(pairs) == []


def test_no_candidate_when_output_equals_input_trivially():
    pairs = [
        Pair(input=[[1, 2]], output=[[1, 2]]),
    ]
    assert detect_tile_hypotheses(pairs) == []


def test_no_candidate_when_tiled_content_does_not_match_output():
    pairs = [
        Pair(input=[[1, 2]], output=[[9, 9, 9, 9]]),
    ]
    assert detect_tile_hypotheses(pairs) == []


def test_apply_tile_hypothesis():
    hypothesis = TileRepeat(2, 1)
    grid = [[1, 2], [3, 4]]
    assert apply_tile_hypothesis(hypothesis, grid) == [[1, 2], [3, 4], [1, 2], [3, 4]]
