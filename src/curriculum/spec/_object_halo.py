"""Halo of an object: the background ring around its members (ADR 0084).

Used by the `Halo` transform op. Pure geometry plus the clipped/protected
painting rule; the interpreter only wires it to the output grid.
"""
from typing import Any, List, Optional, Set, Tuple

from src.curriculum.spec._region_value import RegionValue

_N4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_N8 = _N4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))


def halo_offsets(cells: List[List[Any]], diagonal: bool) -> Set[Tuple[int, int]]:
    """(row, col) offsets relative to the region origin (may be -1 or
    rows/cols) of every non-member cell adjacent to a member cell."""
    neighbours = _N8 if diagonal else _N4
    members = {(r, c) for r, row in enumerate(cells) for c, v in enumerate(row) if v is not None}
    ring = {(r + dr, c + dc) for r, c in members for dr, dc in neighbours}
    return ring - members


def _clipped_box(region: RegionValue, rows: int, cols: int) -> Optional[Tuple[int, int, int, int]]:
    top, left = max(0, region.row0 - 1), max(0, region.col0 - 1)
    bottom = min(rows, region.row0 + region.rows + 1)
    right = min(cols, region.col0 + region.cols + 1)
    if bottom <= top or right <= left:
        return None
    return top, left, bottom, right


def halo_region(
    region: RegionValue, color: int, diagonal: bool, background: int, grid: List[List[int]]
) -> RegionValue:
    """Padded, grid-clipped box whose cells are `color` on ring cells that
    are currently `background` in `grid` and None everywhere else."""
    rows, cols = len(grid), len(grid[0])
    box = _clipped_box(region, rows, cols)
    if box is None:
        return RegionValue(row0=region.row0, col0=region.col0, rows=0, cols=0, cells=[])
    top, left, bottom, right = box
    ring = halo_offsets(region.cells, diagonal)
    painted = {
        (region.row0 + r, region.col0 + c)
        for r, c in ring
        if 0 <= region.row0 + r < rows and 0 <= region.col0 + c < cols
        and grid[region.row0 + r][region.col0 + c] == background
    }
    cells = [
        [color if (r, c) in painted else None for c in range(left, right)]
        for r in range(top, bottom)
    ]
    return RegionValue(row0=top, col0=left, rows=bottom - top, cols=right - left, cells=cells)
