"""Grid type and pure grid utilities for the curricular solver line.

Deliberately self-contained: the curricular line (src/curriculum/) does
not import from src/utils/ or src/solvers/, per ADR 0061's reuse
decisions (RN-CUR-02, reuse only with certainty). The type itself
(a rectangular list-of-lists of ints 0-9) is trivial enough that
redefining it here, rather than depending on the prior line's
src/utils/grid_types.py, keeps the curricular tree independently
buildable and independently testable.
"""
from typing import List

Grid = List[List[int]]

MIN_COLOR = 0
MAX_COLOR = 9


def grid_dims(grid: Grid) -> tuple:
    """Return (num_rows, num_cols). Raises ValueError on a ragged grid."""
    if not grid:
        raise ValueError("grid has zero rows")
    num_cols = len(grid[0])
    for row in grid:
        if len(row) != num_cols:
            raise ValueError("grid is ragged: rows have differing lengths")
    return len(grid), num_cols


def is_valid_grid(grid: Grid) -> bool:
    """True iff grid is non-empty, rectangular, and every cell is 0-9."""
    try:
        grid_dims(grid)
    except ValueError:
        return False
    if not grid or not grid[0]:
        return False
    return all(MIN_COLOR <= cell <= MAX_COLOR for row in grid for cell in row)


def grids_equal(a: Grid, b: Grid) -> bool:
    """Exact cell-by-cell equality, including shape. No partial credit."""
    return a == b


def deep_copy_grid(grid: Grid) -> Grid:
    return [row[:] for row in grid]


def empty_grid(num_rows: int, num_cols: int, fill: int = 0) -> Grid:
    if num_rows <= 0 or num_cols <= 0:
        raise ValueError("num_rows and num_cols must be positive")
    if not (MIN_COLOR <= fill <= MAX_COLOR):
        raise ValueError(f"fill color must be in [{MIN_COLOR}, {MAX_COLOR}]")
    return [[fill for _ in range(num_cols)] for _ in range(num_rows)]
