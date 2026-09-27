"""Whole-grid geometry signatures (ADR 0093). Train pairs only (RN-CUR-03/05).

`geometric_family`: every pair's output is a flip/rotation/transposition
of its input. `completion_family`: every changed cell of every pair is
explained by a mirror or a shift of an unchanged cell of the input, i.e.
the output completes a symmetry or a periodic pattern.
"""
from typing import Callable, Dict, List, Optional, Tuple

Grid = List[List[int]]
Cell = Tuple[int, int]
_PREFILTER = 5
_MIN_CHANGED = 4
_MAX_SYMMETRY_MAPS = 3
_MAX_PERIOD_MAPS = 2


def _hflip(g: Grid) -> Grid:
    return [row[::-1] for row in g]


def _vflip(g: Grid) -> Grid:
    return g[::-1]


def _transpose(g: Grid) -> Grid:
    return [list(col) for col in zip(*g)]


def _rot90(g: Grid) -> Grid:
    return _hflip(_transpose(g))


_FAMILIES: Dict[str, List[Callable[[Grid], Grid]]] = {
    "espelhar": [_hflip, _vflip],
    "girar": [_rot90, lambda g: _rot90(_rot90(g)), lambda g: _rot90(_rot90(_rot90(g)))],
    "transpor": [_transpose, lambda g: _vflip(_hflip(_transpose(g)))],
}


def geometric_family(train: List[Dict]) -> Optional[str]:
    for family, fns in _FAMILIES.items():
        if all(any(fn(p["input"]) == p["output"] for fn in fns) for p in train):
            return family
    return None


def _mirror_maps(h: int, w: int) -> List[Callable[[int, int], Cell]]:
    maps = [lambda r, c, s=s: (s - r, c) for s in range(2 * h - 1)]
    maps += [lambda r, c, s=s: (r, s - c) for s in range(2 * w - 1)]
    maps += [lambda r, c, a=a, b=b: (a - r, b - c) for a in range(2 * h - 1) for b in range(2 * w - 1)]
    maps += [lambda r, c, d=d: (c + d, r - d) for d in range(-w, h)]
    maps += [lambda r, c, s=s: (s - c, s - r) for s in range(h + w - 1)]
    return maps


def _shift_maps(h: int, w: int) -> List[Callable[[int, int], Cell]]:
    maps = []
    for dr in range(0, h // 2 + 1):
        for dc in range(-(w // 2), w // 2 + 1):
            if (dr, dc) == (0, 0) or (dr == 0 and dc < 0):
                continue
            maps += [lambda r, c, k=k, dr=dr, dc=dc: (r + k * dr, c + k * dc) for k in (1, -1, 2, -2, 3, -3)]
    return maps


def _explains(m, cell: Cell, pair: Dict, changed: set) -> bool:
    a, b = pair["input"], pair["output"]
    r, c = m(*cell)
    return 0 <= r < len(a) and 0 <= c < len(a[0]) and (r, c) not in changed and a[r][c] == b[cell[0]][cell[1]]


def _covered(maps, cells: List[Cell], pair: Dict, changed: set) -> List[set]:
    head = cells[:_PREFILTER]
    good = [m for m in maps if any(_explains(m, cell, pair, changed) for cell in head)]
    return [{cell for cell in cells if _explains(m, cell, pair, changed)} for m in good]


def _greedy_cover(sets: List[set], universe: set, limit: int) -> bool:
    remaining = set(universe)
    for _ in range(limit):
        best = max(sets, key=lambda s: len(s & remaining), default=set())
        if not best & remaining:
            return False
        remaining -= best
        if not remaining:
            return True
    return False


def _pair_completes(pair: Dict, maps_for_shape, limit: int) -> bool:
    a, b = pair["input"], pair["output"]
    if len(a) != len(b) or len(a[0]) != len(b[0]):
        return False
    cells = [(r, c) for r in range(len(a)) for c in range(len(a[0])) if a[r][c] != b[r][c]]
    if len(cells) < _MIN_CHANGED:
        return False
    return _greedy_cover(_covered(maps_for_shape(len(a), len(a[0])), cells, pair, set(cells)), set(cells), limit)


def completion_family(train: List[Dict]) -> Optional[str]:
    """"simetria_completar" or "periodico_completar" (the latter has no
    concept-map entry yet), else None."""
    if all(_pair_completes(p, _mirror_maps, _MAX_SYMMETRY_MAPS) for p in train):
        return "simetria_completar"
    if all(_pair_completes(p, _shift_maps, _MAX_PERIOD_MAPS) for p in train):
        return "periodico_completar"
    return None
