"""Honest exact-match evaluation, PRD Section 9.1.

No partial credit: a predicted grid counts as correct only if it is
cell-for-cell and shape identical to the gabarito. This module is the
only place a solver's predictions are ever compared against solutions.py
output, keeping the RN-CUR-03 boundary in one place.
"""
from typing import List

from src.curriculum.grid import Grid, grids_equal


def is_exact_match(predicted: Grid, expected: Grid) -> bool:
    return grids_equal(predicted, expected)


def score_task(predictions: List[Grid], solutions: List[Grid]) -> dict:
    """Score one task's test predictions against its gabaritos.

    predictions and solutions must be the same length (one prediction
    per test pair, no attempt-count logic here - that belongs to a
    future Kaggle-format layer, out of scope before Stage 7).
    """
    if len(predictions) != len(solutions):
        raise ValueError(
            f"predictions/solutions length mismatch: "
            f"{len(predictions)} vs {len(solutions)}"
        )
    matches = [
        is_exact_match(pred, sol) for pred, sol in zip(predictions, solutions)
    ]
    return {
        "num_test_pairs": len(solutions),
        "num_exact_matches": sum(matches),
        "all_exact_match": all(matches) if matches else False,
        "per_pair_match": matches,
    }
