"""Derivation operators of the derived-parameter layer (ADR 0107).

Each operator turns a set of values into one parameter: extremum (ties select
every region reaching it, see `_select_where.py`), unique value, mode, total,
grid colour resources, and a learned table lookup. Pure functions, independent
of `library/` and `perception/` (RN-CUR-14). An operator that has no single
answer raises `InterpreterError`: a derivation never guesses.
"""
from collections import Counter
from typing import Any, Dict, List, Sequence, Tuple

from src.curriculum.grid import Grid
from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._measures import measure_value
from src.curriculum.spec._region_value import RegionValue

REGION_OPS = ("min", "max", "unique", "mode", "total")
GRID_OPS = ("rarest_color", "common_color")
DERIVE_OPS = REGION_OPS + GRID_OPS

Table = Tuple[Tuple[Tuple[int, ...], int], ...]


def _unique(values: List[int]) -> int:
    once = [v for v, n in Counter(values).items() if n == 1]
    if len(once) != 1:
        raise InterpreterError(f"derive unique: {len(once)} values occur exactly once, expected 1")
    return once[0]


def _mode(values: List[int]) -> int:
    ranked = Counter(values).most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        raise InterpreterError("derive mode: tie for the most frequent value")
    return ranked[0][0]


_VALUE_OPS = {"min": min, "max": max, "unique": _unique, "mode": _mode, "total": sum}


def derive_from_regions(items: List[RegionValue], op: str, name: str, arg: Any = 0) -> int:
    if op not in _VALUE_OPS:
        raise InterpreterError(f"derive: unknown region operator {op!r}")
    if not items:
        raise InterpreterError(f"derive {op}: empty region list")
    return _VALUE_OPS[op]([measure_value(item, name, arg) for item in items])


def _grid_cells(grid: Any) -> Grid:
    return grid.cells if isinstance(grid, RegionValue) else grid


def derive_from_grid(grid: Any, op: str, background: int) -> int:
    """Colour resource of the grid, ignoring `background`: the rarest or the
    most common colour; a tie or a grid with no other colour is an error."""
    if op not in GRID_OPS:
        raise InterpreterError(f"derive: unknown grid operator {op!r}")
    counts = Counter(v for row in _grid_cells(grid) for v in row if v is not None and v != background)
    if not counts:
        raise InterpreterError(f"derive {op}: grid has no colour besides the background")
    ranked = counts.most_common()
    pick = ranked[0] if op == "common_color" else ranked[-1]
    if sum(1 for _, n in ranked if n == pick[1]) > 1:
        raise InterpreterError(f"derive {op}: tie between colours")
    return pick[0]


def table_lookup(table: Table, key: Sequence[int]) -> int:
    entries: Dict[Tuple[int, ...], int] = dict(table)
    if tuple(key) not in entries:
        raise InterpreterError(f"table lookup: key {tuple(key)} was not seen in the demonstrations")
    return entries[tuple(key)]
