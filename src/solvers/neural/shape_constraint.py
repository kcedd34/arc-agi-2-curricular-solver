"""Deterministic post-processing that forces a predicted grid to a target
shape, for tasks where shape_rule confirms the shape is mechanically
derivable from the input rather than dependent on the model's EOS timing.

Simplest approach chosen (documented in ADR 0025): truncate extra rows/
columns beyond the target, and pad missing rows/columns by repeating the
last existing row/value. Row width is already correct in most sampled
cases (ADR 0024, 18/22), so padding rarely triggers in practice; it exists
for the remaining cases and to keep the function total (never raises on a
short or empty grid).
"""
from src.utils.grid_types import Grid


def force_grid_shape(grid: Grid, target_rows: int, target_cols: int) -> Grid:
    rows = _force_row_count(grid, target_rows, target_cols)
    return [_force_row_width(row, target_cols) for row in rows]


def _force_row_width(row, target_cols):
    if len(row) > target_cols:
        return row[:target_cols]
    if len(row) < target_cols:
        pad_value = row[-1] if row else 0
        return row + [pad_value] * (target_cols - len(row))
    return list(row)


def _force_row_count(grid, target_rows, target_cols):
    if not grid:
        return [[0] * target_cols for _ in range(target_rows)]
    if len(grid) > target_rows:
        return grid[:target_rows]
    if len(grid) < target_rows:
        last_row = grid[-1]
        return grid + [list(last_row) for _ in range(target_rows - len(grid))]
    return grid
