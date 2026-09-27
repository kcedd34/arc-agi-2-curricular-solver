"""Row/column segment partitions (ADR 0098).

A segment is a line (row or column) holding exactly two non-background
cells. Its region spans the two cells, endpoints included; the cells in
between are non-member (None), so `gap` measures them and `between`
resolves exactly them.
"""
from typing import List, Optional

from src.curriculum.grid import Grid, grid_dims
from src.curriculum.spec._region_value import RegionValue


def _line_endpoints(line: List[int], background: int) -> Optional[tuple]:
    hits = [i for i, v in enumerate(line) if v != background]
    return (hits[0], hits[1]) if len(hits) == 2 else None


def _span_cells(line: List[int], first: int, last: int) -> List[Optional[int]]:
    return [line[i] if i in (first, last) else None for i in range(first, last + 1)]


def row_segments(grid: Grid, background: int) -> List[RegionValue]:
    regions = []
    for r, line in enumerate(grid):
        ends = _line_endpoints(list(line), background)
        if ends is None:
            continue
        first, last = ends
        regions.append(
            RegionValue(
                row0=r, col0=first, rows=1, cols=last - first + 1,
                cells=[_span_cells(list(line), first, last)],
            )
        )
    return regions


def col_segments(grid: Grid, background: int) -> List[RegionValue]:
    rows, cols = grid_dims(grid)
    regions = []
    for c in range(cols):
        line = [grid[r][c] for r in range(rows)]
        ends = _line_endpoints(line, background)
        if ends is None:
            continue
        first, last = ends
        regions.append(
            RegionValue(
                row0=first, col0=c, rows=last - first + 1, cols=1,
                cells=[[v] for v in _span_cells(line, first, last)],
            )
        )
    return regions
