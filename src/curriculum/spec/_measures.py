"""Region measures, extremum and select_where semantics (ADR 0098).

Each measure is a pure function region -> int over a `RegionValue`; a
non-member cell is `None`. Independent of `library/` and `perception/`
(RN-CUR-14); equivalence with `perception/objects.py` is checked by a test.
"""
from collections import Counter
from typing import Any, Callable, Dict, List

from src.curriculum.grid import grid_dims
from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._generated import PREFIX, generated_measure
from src.curriculum.spec._key_measures import key_col, key_color, key_row
from src.curriculum.spec._object_holes import enclosed_positions
from src.curriculum.spec._region_value import RegionValue
from src.curriculum.spec._toward import toward_target


def _members(region: RegionValue) -> List[int]:
    return [v for row in region.cells for v in row if v is not None]


def _size(region: RegionValue, arg: Any) -> int:
    return len(_members(region))


def _gap(region: RegionValue, arg: Any) -> int:
    return region.rows * region.cols - len(_members(region))


def _colors(region: RegionValue, arg: Any) -> int:
    return len(set(_members(region)))


def _color(region: RegionValue, arg: Any) -> int:
    colors = set(_members(region))
    if len(colors) != 1:
        raise InterpreterError(f"color: region has {len(colors)} colors, expected exactly 1")
    return next(iter(colors))


def _distance_to(region: RegionValue, arg: Any) -> int:
    return toward_target(region, arg)[1]


def _hole_cells(region: RegionValue, arg: Any) -> int:
    return len(enclosed_positions(region.cells))


def _count_color(region: RegionValue, arg: Any) -> int:
    return sum(1 for v in _members(region) if v == arg)


def _row_parity(region: RegionValue, arg: Any) -> int:
    return region.row0 % 2


def _col_parity(region: RegionValue, arg: Any) -> int:
    return region.col0 % 2


def _dominant_color(region: RegionValue, arg: Any) -> int:
    ranked = Counter(_members(region)).most_common()
    if not ranked:
        raise InterpreterError("dominant_color: region has no member cells")
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        raise InterpreterError("dominant_color: tie for the most common color")
    return ranked[0][0]


def _border_distance(region: RegionValue, arg: Any) -> int:
    rows, cols = grid_dims(_grid_of(arg))
    return min(
        region.row0,
        region.col0,
        rows - (region.row0 + region.rows),
        cols - (region.col0 + region.cols),
    )


def _grid_of(arg: Any) -> Any:
    return arg.cells if isinstance(arg, RegionValue) else arg


def _corner_nw_color(region: RegionValue, arg: Any) -> int:
    """Colour of the cell diagonally outside the bbox's top-left corner; 0
    when that cell falls outside the grid."""
    grid = _grid_of(arg)
    row, col = region.row0 - 1, region.col0 - 1
    rows, cols = grid_dims(grid)
    return grid[row][col] if 0 <= row < rows and 0 <= col < cols else 0


def _closed(region: RegionValue, arg: Any) -> int:
    """1 when the region has an enclosed hole or fills its bbox, else 0."""
    return 1 if _hole_cells(region, arg) > 0 or _gap(region, arg) == 0 else 0


def _multi_cell(region: RegionValue, arg: Any) -> int:
    return 1 if len(_members(region)) > 1 else 0


GRID_ARG_MEASURES = frozenset({"border_distance", "corner_nw_color"})

_MEASURES: Dict[str, Callable[[RegionValue, Any], int]] = {
    "size": _size,
    "width": lambda region, arg: region.cols,
    "height": lambda region, arg: region.rows,
    "gap": _gap,
    "colors": _colors,
    "hole_cells": _hole_cells,
    "border_distance": _border_distance,
    "count_color": _count_color,
    "color": _color,
    "distance_to": _distance_to,
    "row_parity": _row_parity,
    "col_parity": _col_parity,
    "dominant_color": _dominant_color,
    "corner_nw_color": _corner_nw_color,
    "closed": _closed,
    "multi_cell": _multi_cell,
    "key_color": key_color,
    "key_row": key_row,
    "key_col": key_col,
}

MEASURE_NAMES = tuple(_MEASURES)


def measure_value(region: RegionValue, name: str, arg: Any = 0) -> int:
    if name.startswith(PREFIX):
        return generated_measure(region, name[len(PREFIX):])
    if name not in _MEASURES:
        raise InterpreterError(f"measure: unknown measure {name!r}")
    return _MEASURES[name](region, arg)


def extremum_value(items: List[RegionValue], name: str, mode: str, arg: Any = 0) -> int:
    if mode not in ("min", "max"):
        raise InterpreterError(f"extremum: unknown mode {mode!r}")
    if not items:
        raise InterpreterError("extremum: empty region list")
    values = [measure_value(item, name, arg) for item in items]
    return min(values) if mode == "min" else max(values)


def select_where_items(items: List[RegionValue], name: str, value: int, arg: Any = 0) -> List[RegionValue]:
    return [item for item in items if measure_value(item, name, arg) == value]
