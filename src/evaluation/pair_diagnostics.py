"""Per-test-pair error diagnostics: dimension match and per-cell accuracy.

Post-hoc analysis of a solver run, separate from the official exact-match
metric (see metrics.py), which only reports pass/fail per pair.
"""
from typing import List, Optional, Tuple

from src.utils.grid_types import Grid


def dimension_match(predicted: Grid, expected: Grid) -> bool:
    return len(predicted) == len(expected) and all(
        len(pr_row) == len(er_row) for pr_row, er_row in zip(predicted, expected)
    )


def per_cell_accuracy(predicted: Grid, expected: Grid) -> Optional[float]:
    if not dimension_match(predicted, expected):
        return None
    total_cells = sum(len(row) for row in expected)
    if total_cells == 0:
        return None
    matches = sum(
        1
        for pr_row, er_row in zip(predicted, expected)
        for pr_cell, er_cell in zip(pr_row, er_row)
        if pr_cell == er_cell
    )
    return matches / total_cells


def best_pair_diagnostic(predictions: List[Grid], expected: Grid) -> Tuple[bool, Optional[float]]:
    if not predictions:
        return False, None
    any_dimension_match = any(dimension_match(p, expected) for p in predictions)
    accuracies = [a for a in (per_cell_accuracy(p, expected) for p in predictions) if a is not None]
    best_accuracy = max(accuracies) if accuracies else None
    return any_dimension_match, best_accuracy
