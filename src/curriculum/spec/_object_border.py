"""Border/interior classification of an object's own cells (ADR 0081).

Shared by the `RecolorObjectPart` transform op and the `HasInterior`
predicate so both use one definition. A member cell is a non-None cell of
a region; it is a border cell when at least one of its 4-connected
neighbours is outside the region's bounding box or is a non-member (None)
cell, and an interior cell otherwise.
"""
from typing import Any, List, Set, Tuple

_NEIGHBOURS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _is_member(cells: List[List[Any]], row: int, col: int) -> bool:
    inside = 0 <= row < len(cells) and 0 <= col < len(cells[0])
    return inside and cells[row][col] is not None


def _is_interior(cells: List[List[Any]], row: int, col: int) -> bool:
    return all(_is_member(cells, row + dr, col + dc) for dr, dc in _NEIGHBOURS)


def interior_positions(cells: List[List[Any]]) -> Set[Tuple[int, int]]:
    """(row, col) of every member cell whose 4 neighbours are all members."""
    return {
        (r, c)
        for r, row in enumerate(cells)
        for c, value in enumerate(row)
        if value is not None and _is_interior(cells, r, c)
    }


def has_interior(cells: List[List[Any]]) -> bool:
    return bool(interior_positions(cells))
