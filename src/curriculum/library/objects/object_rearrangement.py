"""Rearrangement detection for the connectivity prune (ADR 0092)."""
from collections import Counter

from src.curriculum.loader import Task


def _same_color_histogram(grid_a, grid_b) -> bool:
    if len(grid_a) != len(grid_b) or len(grid_a[0]) != len(grid_b[0]):
        return False
    return Counter(v for row in grid_a for v in row) == Counter(v for row in grid_b for v in row)


def is_rearrangement_task(task: Task) -> bool:
    """Every train pair keeps the shape and the per-color cell counts (so
    cells only moved) yet changes the grid. Object counts are not
    invariant under movement (stacked objects merge), so the count-based
    connectivity prune is unsound for these tasks."""
    if not task.train:
        return False
    return all(
        pair.input != pair.output and _same_color_histogram(pair.input, pair.output)
        for pair in task.train
    )
