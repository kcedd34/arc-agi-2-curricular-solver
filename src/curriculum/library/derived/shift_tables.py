"""Shift table learned between demonstration pairs (ADR 0107): the (dr, dc)
each region moves by is read from the train outputs and keyed by a measure
of the region. Same acceptance bar as the colour tables: one shift per key,
a key that recurs, and more than one distinct shift. A key absent from the
table at test time makes the interpreter fail; a shift is never invented."""
from typing import Dict, List, Optional, Sequence, Set, Tuple

from src.curriculum.grid import Grid, grid_dims
from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._measures import measure_value
from src.curriculum.spec._region_value import RegionValue

SHIFT_KEY_SETS: Tuple[Tuple[str, ...], ...] = (("color",), ("size",), ("height",), ("width",))

Shift = Tuple[int, int]
ShiftTable = Tuple[Tuple[Tuple[int, ...], Shift], ...]


def _members(region: RegionValue) -> List[Tuple[int, int, int]]:
    return [
        (region.row0 + r, region.col0 + c, v)
        for r, row in enumerate(region.cells)
        for c, v in enumerate(row)
        if v is not None
    ]


def shift_candidates(region: RegionValue, out_grid: Grid) -> Set[Shift]:
    """Every shift that lands all member cells on equal colours in the output."""
    rows, cols = grid_dims(out_grid)
    members = _members(region)
    found = set()
    for dr in range(-rows + 1, rows):
        for dc in range(-cols + 1, cols):
            if all(
                0 <= r + dr < rows and 0 <= c + dc < cols and out_grid[r + dr][c + dc] == v
                for r, c, v in members
            ):
                found.add((dr, dc))
    return found


def _pick(candidates: Set[Shift]) -> Shift:
    return min(candidates, key=lambda s: (abs(s[0]) + abs(s[1]), s))


def _key(region: RegionValue, measures: Sequence[str]) -> Tuple[int, ...]:
    return tuple(measure_value(region, m) for m in measures)


def learn_shift_table(observations: List[Tuple[RegionValue, Grid]], measures: Sequence[str]) -> Optional[ShiftTable]:
    """`observations`: (region, output grid) for every moving region."""
    allowed: Dict[Tuple[int, ...], Set[Shift]] = {}
    counts: Dict[Tuple[int, ...], int] = {}
    try:
        for region, out_grid in observations:
            key = _key(region, measures)
            cands = shift_candidates(region, out_grid)
            allowed[key] = allowed[key] & cands if key in allowed else cands
            counts[key] = counts.get(key, 0) + 1
    except (InterpreterError, ValueError, KeyError):
        return None
    if not allowed or any(not cands for cands in allowed.values()):
        return None
    table = {key: _pick(cands) for key, cands in allowed.items()}
    if len(set(table.values())) < 2 or max(counts.values()) < 2:
        return None
    return tuple(sorted(table.items()))
