from src.solvers.symmetry_heuristics import (
    SymmetryHeuristic,
    apply_symmetry_heuristic,
    detect_symmetry_heuristics,
)
from src.utils.task_loader import Pair


def test_detects_as_found_anomaly():
    # Single row, width 3: mirror_horizontal mismatches at col0 and col2
    # (two separate 1-cell regions, not adjacent since col1 matches).
    # region_index=0 -> col0 (value 1), as_found reads it straight.
    pairs = [Pair(input=[[1, 2, 3]], output=[[1]])]
    hypotheses = detect_symmetry_heuristics(pairs)
    assert SymmetryHeuristic("mirror_horizontal", 0, "as_found") in hypotheses


def test_detects_repaired_anomaly():
    # Same grid: region_index=0 (col0), "repaired" reads the mirrored
    # grid's value at that position (col0 of [3, 2, 1] = 3).
    pairs = [Pair(input=[[1, 2, 3]], output=[[3]])]
    hypotheses = detect_symmetry_heuristics(pairs)
    assert SymmetryHeuristic("mirror_horizontal", 0, "repaired") in hypotheses


def test_no_candidate_when_perfectly_symmetric():
    pairs = [Pair(input=[[1, 2, 1], [3, 4, 3]], output=[[9]])]
    assert detect_symmetry_heuristics(pairs) == []


def test_no_candidate_when_mismatches_split_into_more_than_two_regions():
    # Width 7, only cols 0/2/4/6 mismatch (cols 1/3/5 coincide with their
    # mirror partner), so the mask has 4 isolated single-cell regions -
    # more than the 2 this heuristic tolerates.
    pairs = [Pair(input=[[1, 9, 3, 4, 5, 9, 7]], output=[[9]])]
    assert detect_symmetry_heuristics(pairs) == []


def test_apply_symmetry_heuristic_directly():
    heuristic = SymmetryHeuristic("mirror_horizontal", 0, "repaired")
    grid = [[1, 2, 3]]
    assert apply_symmetry_heuristic(heuristic, grid) == [[3]]
