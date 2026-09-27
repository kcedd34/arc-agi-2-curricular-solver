"""Hole classification of an object's bounding box (ADR 0082).

A hole cell is a non-member (None) cell of a region that cannot reach the
outside of the region's bounding box through 4-connected moves over
non-member cells. Shared by the `FillEnclosed` transform op and the
`HasHole` predicate so both use one definition.
"""
from collections import deque
from typing import Any, List, Set, Tuple

_NEIGHBOURS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _open_border_seeds(cells: List[List[Any]]) -> List[Tuple[int, int]]:
    rows, cols = len(cells), len(cells[0])
    return [
        (r, c)
        for r in range(rows)
        for c in range(cols)
        if cells[r][c] is None and (r in (0, rows - 1) or c in (0, cols - 1))
    ]


def _reachable_from_outside(cells: List[List[Any]]) -> Set[Tuple[int, int]]:
    rows, cols = len(cells), len(cells[0])
    seen = set(_open_border_seeds(cells))
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for dr, dc in _NEIGHBOURS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and cells[nr][nc] is None and (nr, nc) not in seen:
                seen.add((nr, nc))
                queue.append((nr, nc))
    return seen


def enclosed_positions(cells: List[List[Any]]) -> Set[Tuple[int, int]]:
    """(row, col) of every non-member cell not reachable from outside."""
    outside = _reachable_from_outside(cells)
    return {
        (r, c)
        for r, row in enumerate(cells)
        for c, value in enumerate(row)
        if value is None and (r, c) not in outside
    }


def has_hole(cells: List[List[Any]]) -> bool:
    return bool(enclosed_positions(cells))
