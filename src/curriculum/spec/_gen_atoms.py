"""Atomic properties of generated measures (ADR 0110).

Own atoms read one region; sibling atoms aggregate a relation between the
region and the other regions of its partition. Every function returns an int
and raises `InterpreterError` when it has no answer. Independent of
`library/` and `perception/` (RN-CUR-14).
"""
from collections import Counter
from typing import Callable, Dict, List, Tuple

from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._object_holes import enclosed_positions
from src.curriculum.spec._region_value import RegionValue

INT, COLOR, BOOL = "int", "color", "bool"
MAX_SIBLINGS = 48


def _members(region: RegionValue) -> List[int]:
    cached = region.memo.get("_members")
    if cached is None:
        cached = region.memo["_members"] = [v for row in region.cells for v in row if v is not None]
    return cached


def _size(r: RegionValue) -> int:
    return len(_members(r))


def _bbox_area(r: RegionValue) -> int:
    return r.rows * r.cols


def _color(r: RegionValue) -> int:
    colors = set(_members(r))
    if len(colors) != 1:
        raise InterpreterError("color: region is not single-coloured")
    return next(iter(colors))


def _dominant(r: RegionValue) -> int:
    ranked = Counter(_members(r)).most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        raise InterpreterError("dominant_color: tie")
    return ranked[0][0]


def _border_distance(r: RegionValue) -> int:
    if r.ctx is None:
        raise InterpreterError("bdist: region has no grid context")
    rows, cols = r.ctx.dims
    return min(r.row0, r.col0, rows - r.row0 - r.rows, cols - r.col0 - r.cols)


def _n_regions(r: RegionValue) -> int:
    if r.ctx is None:
        raise InterpreterError("nreg: region has no partition context")
    return len(r.ctx.regions)


OWN_ATOMS: Dict[str, Tuple[str, Callable[[RegionValue], int]]] = {
    "size": (INT, _size),
    "width": (INT, lambda r: r.cols),
    "height": (INT, lambda r: r.rows),
    "gap": (INT, lambda r: _bbox_area(r) - _size(r)),
    "bbox_area": (INT, _bbox_area),
    "colors": (INT, lambda r: len(set(_members(r)))),
    "hole_cells": (INT, lambda r: len(enclosed_positions(r.cells))),
    "row0": (INT, lambda r: r.row0),
    "col0": (INT, lambda r: r.col0),
    "row1": (INT, lambda r: r.row0 + r.rows - 1),
    "col1": (INT, lambda r: r.col0 + r.cols - 1),
    "row_c": (INT, lambda r: 2 * r.row0 + r.rows - 1),
    "col_c": (INT, lambda r: 2 * r.col0 + r.cols - 1),
    "row_par": (INT, lambda r: r.row0 % 2),
    "col_par": (INT, lambda r: r.col0 % 2),
    "density": (INT, lambda r: _size(r) * 100 // _bbox_area(r)),
    "bdist": (INT, _border_distance),
    "nreg": (INT, _n_regions),
    "color": (COLOR, _color),
    "dominant_color": (COLOR, _dominant),
}


def _row_gap(a: RegionValue, s: RegionValue) -> int:
    return max(s.row0 - (a.row0 + a.rows - 1), a.row0 - (s.row0 + s.rows - 1), 0)


def _col_gap(a: RegionValue, s: RegionValue) -> int:
    return max(s.col0 - (a.col0 + a.cols - 1), a.col0 - (s.col0 + s.cols - 1), 0)


def _overlap(a: RegionValue, s: RegionValue) -> int:
    dr = min(a.row0 + a.rows, s.row0 + s.rows) - max(a.row0, s.row0)
    dc = min(a.col0 + a.cols, s.col0 + s.cols) - max(a.col0, s.col0)
    return max(dr, 0) * max(dc, 0)


def _contains(a: RegionValue, s: RegionValue) -> int:
    inside = (
        a.row0 <= s.row0 and a.col0 <= s.col0
        and s.row0 + s.rows <= a.row0 + a.rows and s.col0 + s.cols <= a.col0 + a.cols
    )
    return 1 if inside else 0


RELATIONS: Dict[str, Callable[[RegionValue, RegionValue], int]] = {
    "dist": lambda a, s: max(_row_gap(a, s), _col_gap(a, s)),
    "cdist": lambda a, s: abs((2 * a.row0 + a.rows) - (2 * s.row0 + s.rows))
    + abs((2 * a.col0 + a.cols) - (2 * s.col0 + s.cols)),
    "overlap": _overlap,
    "sizediff": lambda a, s: _size(a) - _size(s),
    "aligned": lambda a, s: 1 if _overlap_axis(a, s) else 0,
    "contains": _contains,
    "inside": lambda a, s: _contains(s, a),
}


def _overlap_axis(a: RegionValue, s: RegionValue) -> bool:
    return _row_gap(a, s) == 0 or _col_gap(a, s) == 0


INT_AGG_RELATIONS = ("dist", "cdist", "overlap", "sizediff")
FLAG_RELATIONS = ("aligned", "contains", "inside")
AGGREGATES = {"min": min, "max": max, "sum": sum}


def sibling_atom_names() -> List[Tuple[str, str, str, str]]:
    """(atom name, type, aggregate, relation) of every sibling atom."""
    found = [
        (f"{agg}_{rel}", INT, agg, rel) for rel in INT_AGG_RELATIONS for agg in AGGREGATES
    ]
    found += [(f"any_{rel}", BOOL, "max", rel) for rel in FLAG_RELATIONS]
    found += [(f"cnt_{rel}", INT, "sum", rel) for rel in FLAG_RELATIONS]
    return found


def _others(region: RegionValue) -> List[RegionValue]:
    ctx = region.ctx
    if ctx is None:
        raise InterpreterError("sibling atom: region has no partition context")
    if len(ctx.regions) > MAX_SIBLINGS:
        raise InterpreterError(f"sibling atom: more than {MAX_SIBLINGS} regions")
    return [s for i, s in enumerate(ctx.regions) if i != ctx.index]


def sibling_value(region: RegionValue, agg: str, rel: str) -> int:
    others = _others(region)
    values = [RELATIONS[rel](region, s) for s in others]
    if not values:
        if agg == "sum":
            return 0
        if rel in FLAG_RELATIONS:
            return 0
        raise InterpreterError("sibling atom: no sibling regions")
    return AGGREGATES[agg](values)


SIBLING_ATOMS: Dict[str, Tuple[str, str, str]] = {
    name: (typ, agg, rel) for name, typ, agg, rel in sibling_atom_names()
}


def atom_type(name: str) -> str:
    return OWN_ATOMS[name][0] if name in OWN_ATOMS else SIBLING_ATOMS[name][0]


def is_atom(name: str) -> bool:
    return name in OWN_ATOMS or name in SIBLING_ATOMS


def atom_value(region: RegionValue, name: str) -> int:
    if name in OWN_ATOMS:
        return OWN_ATOMS[name][1](region)
    _, agg, rel = SIBLING_ATOMS[name]
    return sibling_value(region, agg, rel)


ATOM_NAMES: Tuple[str, ...] = tuple(OWN_ATOMS) + tuple(SIBLING_ATOMS)
