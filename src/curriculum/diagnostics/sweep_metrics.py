"""Pure helpers for the scale sweep (ADR 0093): compare predictions with
gabaritos without any solver logic. Only called post-hoc, like
`verified_verdict.py` (RN-CUR-03)."""
from typing import List, Optional

from src.curriculum.grid import Grid, grids_equal


def wrong_cells(prediction: Grid, expected: Grid) -> Optional[int]:
    """Number of differing cells, or None when the shapes differ."""
    if len(prediction) != len(expected) or len(prediction[0]) != len(expected[0]):
        return None
    return sum(a != b for pr, er in zip(prediction, expected) for a, b in zip(pr, er))


def task_wrong_cells(predictions: List[Grid], solutions: List[Grid]) -> Optional[int]:
    """Total differing cells over every test pair, None if any shape differs."""
    total = 0
    for prediction, expected in zip(predictions, solutions):
        cells = wrong_cells(prediction, expected)
        if cells is None:
            return None
        total += cells
    return total


def matches_all(predictions: List[Grid], solutions: List[Grid]) -> bool:
    return len(predictions) == len(solutions) and all(
        grids_equal(p, s) for p, s in zip(predictions, solutions)
    )


def first_matching_rank(ranked, solutions: List[Grid]) -> Optional[int]:
    """1-based rank of the first candidate whose predictions equal the
    gabarito, or None when no verified candidate does."""
    for index, (_composition, predictions) in enumerate(ranked, start=1):
        if matches_all(predictions, solutions):
            return index
    return None


def best_attempt_wrong_cells(attempts: List[List[Grid]], solutions: List[Grid]) -> Optional[int]:
    """Smallest wrong-cell count among the attempts; None when no attempt
    has the right shape."""
    counts = [task_wrong_cells(a, solutions) for a in attempts]
    counts = [c for c in counts if c is not None]
    return min(counts) if counts else None
