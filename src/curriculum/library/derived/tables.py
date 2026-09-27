"""Table learned between demonstration pairs (ADR 0107).

For an action that paints its selected regions with a colour, the colour each
region ends with is read from the train outputs and keyed by measures of the
region. A table is accepted only when it is consistent (one colour per key),
has keys that recur on average at least twice (evidence of a rule, not memorisation) and more than
one colour (otherwise a literal already explains it). Keys absent from the
table at test time make the interpreter fail; a value is never invented."""
from typing import Dict, List, Optional, Sequence, Tuple

from src.curriculum.grid import Grid
from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._measures import measure_value
from src.curriculum.spec._region_value import RegionValue

KEY_SETS: Tuple[Tuple[str, ...], ...] = (
    ("size",), ("width",), ("height",), ("hole_cells",), ("colors",), ("row_parity",), ("col_parity",),
    ("closed",), ("size", "width"), ("size", "height"), ("width", "height"), ("row_parity", "col_parity"),
)

Table = Tuple[Tuple[Tuple[int, ...], int], ...]


def _region_colour(region: RegionValue, in_grid: Grid, out_grid: Grid) -> Optional[int]:
    """The colour the region's member cells hold in the output, when uniform."""
    seen = set()
    for r, row in enumerate(region.cells):
        for c, member in enumerate(row):
            if member is not None:
                seen.add(out_grid[region.row0 + r][region.col0 + c])
    return next(iter(seen)) if len(seen) == 1 else None


def _key(region: RegionValue, measures: Sequence[str]) -> Tuple[int, ...]:
    return tuple(measure_value(region, m) for m in measures)


def learn_color_table(observations: List[Tuple[RegionValue, Grid, Grid]], measures: Sequence[str]) -> Optional[Table]:
    """`observations`: (region, input, output) for every selected region."""
    table: Dict[Tuple[int, ...], int] = {}
    counts: Dict[Tuple[int, ...], int] = {}
    try:
        for region, in_grid, out_grid in observations:
            colour = _region_colour(region, in_grid, out_grid)
            key = _key(region, measures)
            if colour is None or table.setdefault(key, colour) != colour:
                return None
            counts[key] = counts.get(key, 0) + 1
    except (InterpreterError, ValueError, KeyError):
        return None
    if len(set(table.values())) < 2 or sum(counts.values()) < 2 * len(table):
        return None
    return tuple(sorted(table.items()))
