"""Train-pair signature classifiers used to split loose concept tags into
rule families (ADR 0085). Only the train pairs of a task are read
(RN-CUR-03/05); nothing here touches test outputs or the answer key.

Each classifier takes a task's train pairs (dicts with "input"/"output"
grids) and answers whether every pair fits one narrow rule family.
"""
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple

Grid = List[List[int]]
Cell = Tuple[int, int]

_N4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_N8 = _N4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))


def background_color(grid: Grid) -> int:
    return Counter(v for row in grid for v in row).most_common(1)[0][0]


def same_shape(pair: Dict) -> bool:
    a, b = pair["input"], pair["output"]
    return len(a) == len(b) and len(a[0]) == len(b[0])


def changed_cells(pair: Dict) -> List[Cell]:
    a, b = pair["input"], pair["output"]
    return [(r, c) for r in range(len(a)) for c in range(len(a[0])) if a[r][c] != b[r][c]]


def _foreground(grid: Grid, bg: int) -> Set[Cell]:
    return {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != bg}


def pure_additions(pair: Dict) -> Optional[List[Cell]]:
    """Changed cells when every one turns background into foreground."""
    if not same_shape(pair):
        return None
    bg = background_color(pair["input"])
    diff = changed_cells(pair)
    if not diff or any(pair["input"][r][c] != bg for r, c in diff):
        return None
    return diff


def _adjacent_to(cells: List[Cell], foreground: Set[Cell], neighbours) -> bool:
    return all(any((r + dr, c + dc) in foreground for dr, dc in neighbours) for r, c in cells)


def is_halo_family(train: List[Dict]) -> bool:
    """Every pair only adds cells 8-adjacent to existing foreground."""
    for pair in train:
        diff = pure_additions(pair)
        if diff is None:
            return False
        if not _adjacent_to(diff, _foreground(pair["input"], background_color(pair["input"])), _N8):
            return False
    return True


def _shares_line(cell: Cell, foreground: Set[Cell]) -> bool:
    r, c = cell
    return any(
        fr == r or fc == c or fr - fc == r - c or fr + fc == r + c
        for fr, fc in foreground
    )


def is_marker_line_family(train: List[Dict]) -> bool:
    """Pure additions, not a halo, every added cell on a row/column/diagonal
    of some foreground cell (rays and connections between markers)."""
    if is_halo_family(train):
        return False
    for pair in train:
        diff = pure_additions(pair)
        if diff is None:
            return False
        fg = _foreground(pair["input"], background_color(pair["input"]))
        if not all(_shares_line(cell, fg) for cell in diff):
            return False
    return True


def _nearest_colors(grid: Grid, r: int, c: int, dr: int, dc: int, bg: int) -> Optional[int]:
    r, c = r + dr, c + dc
    while 0 <= r < len(grid) and 0 <= c < len(grid[0]):
        if grid[r][c] != bg:
            return grid[r][c]
        r, c = r + dr, c + dc
    return None


def _cell_connects(pair: Dict, cell: Cell, bg: int) -> bool:
    r, c = cell
    a = pair["input"]
    for (d1, d2) in (((0, -1), (0, 1)), ((-1, 0), (1, 0))):
        first, second = _nearest_colors(a, r, c, *d1, bg), _nearest_colors(a, r, c, *d2, bg)
        if first is not None and first == second == pair["output"][r][c]:
            return True
    return False


def is_connect_family(train: List[Dict]) -> bool:
    """Pure additions where every added cell sits between two same-colored
    input cells (same row or column) and takes that color."""
    for pair in train:
        diff = pure_additions(pair)
        if diff is None:
            return False
        bg = background_color(pair["input"])
        if not all(_cell_connects(pair, cell, bg) for cell in diff):
            return False
    return True


def _pair_offset(pair: Dict) -> Optional[Cell]:
    if not same_shape(pair):
        return None
    bg = background_color(pair["input"])
    a, b = pair["input"], pair["output"]
    diff = changed_cells(pair)
    removed = {(r, c) for r, c in diff if a[r][c] != bg}
    added = {(r, c) for r, c in diff if b[r][c] != bg}
    if not removed or len(removed) != len(added):
        return None
    dr, dc = min(added)[0] - min(removed)[0], min(added)[1] - min(removed)[1]
    if (dr, dc) == (0, 0):
        return None
    return (dr, dc) if {(r + dr, c + dc) for r, c in removed} == added else None


def is_translation_family(train: List[Dict]) -> bool:
    """Every pair moves foreground cells by the same nonzero offset."""
    offsets = {_pair_offset(pair) for pair in train}
    return len(offsets) == 1 and None not in offsets


def output_shape_kind(train: List[Dict]) -> str:
    """"same" (all pairs keep the shape), "scalar" (all outputs 1x1),
    "smaller" (all outputs strictly smaller), "other"."""
    if all(same_shape(p) for p in train):
        return "same"
    if all(len(p["output"]) == 1 and len(p["output"][0]) == 1 for p in train):
        return "scalar"
    if all(len(p["output"]) <= len(p["input"]) and len(p["output"][0]) <= len(p["input"][0]) for p in train):
        return "smaller"
    return "other"


def _pair_diff_kind(pair: Dict) -> str:
    if not same_shape(pair):
        return "reshape"
    bg = background_color(pair["input"])
    a, b = pair["input"], pair["output"]
    diff = changed_cells(pair)
    if not diff:
        return "none"
    kinds = {("add" if a[r][c] == bg else "remove" if b[r][c] == bg else "recolor") for r, c in diff}
    return kinds.pop() if len(kinds) == 1 else "mixed"


def diff_kind(train: List[Dict]) -> str:
    """"add", "remove", "recolor" or "mixed" when uniform across pairs,
    "varied" otherwise, "reshape" when any pair changes shape."""
    kinds = {_pair_diff_kind(p) for p in train}
    if "reshape" in kinds:
        return "reshape"
    return kinds.pop() if len(kinds) == 1 else "varied"


def _foreground_counts(grid: Grid) -> Counter:
    bg = background_color(grid)
    return Counter(v for row in grid for v in row if v != bg)


def _pair_paints_extreme_color(pair: Dict, most: bool) -> bool:
    counts = _foreground_counts(pair["input"])
    if len(counts) < 2:
        return False
    pick = max if most else min
    target = pick(counts.values())
    if list(counts.values()).count(target) != 1:
        return False
    color = next(c for c, n in counts.items() if n == target)
    b = pair["output"]
    diff = changed_cells(pair)
    return bool(diff) and all(b[r][c] == color for r, c in diff)


def paints_frequency_extreme(train: List[Dict]) -> Optional[str]:
    """"most" / "least" when every changed cell of every pair takes the
    input's unique most / least frequent foreground color, else None."""
    for label, most in (("most", True), ("least", False)):
        if all(same_shape(p) and _pair_paints_extreme_color(p, most) for p in train):
            return label
    return None


def rule_family(train: List[Dict]) -> Optional[str]:
    """Narrow rule family of a task from its train pairs, or None when no
    signature applies ("halo", "connect", "marker_line", "translation", "freq_most",
    "freq_least")."""
    if is_halo_family(train):
        return "halo"
    if is_connect_family(train):
        return "connect"
    if is_marker_line_family(train):
        return "marker_line"
    if is_translation_family(train):
        return "translation"
    extreme = paints_frequency_extreme(train)
    return f"freq_{extreme}" if extreme else None
