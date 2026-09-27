"""Region and ray signatures for pure-addition tasks (ADR 0093). Train
pairs only (RN-CUR-03/05). Reuses `tag_signatures` helpers."""
from typing import Dict, List, Set, Tuple

from src.curriculum.tag_signatures import background_color, pure_additions

Cell = Tuple[int, int]


def _enclosed_background(grid, bg: int) -> Set[Cell]:
    """Background cells 4-connected components that never touch the border."""
    h, w = len(grid), len(grid[0])
    seen: Set[Cell] = set()
    enclosed: Set[Cell] = set()
    for r0 in range(h):
        for c0 in range(w):
            if (r0, c0) in seen or grid[r0][c0] != bg:
                continue
            component, touches = _flood(grid, bg, (r0, c0), seen)
            if not touches:
                enclosed |= component
    return enclosed


def _flood(grid, bg: int, start: Cell, seen: Set[Cell]):
    h, w = len(grid), len(grid[0])
    stack, component, touches = [start], set(), False
    seen.add(start)
    while stack:
        r, c = stack.pop()
        component.add((r, c))
        touches |= r in (0, h - 1) or c in (0, w - 1)
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == bg:
                seen.add((nr, nc))
                stack.append((nr, nc))
    return component, touches


def is_enclosed_fill_family(train: List[Dict]) -> bool:
    """Every pair only paints background cells that no path of background
    connects to the border."""
    for pair in train:
        added = pure_additions(pair)
        if added is None:
            return False
        if not set(added) <= _enclosed_background(pair["input"], background_color(pair["input"])):
            return False
    return True


def _has_ray_source(pair: Dict, cell: Cell, added: Set[Cell]) -> bool:
    a, b = pair["input"], pair["output"]
    bg = background_color(a)
    r, c = cell
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        while 0 <= nr < len(a) and 0 <= nc < len(a[0]) and (a[nr][nc] == bg and (nr, nc) in added):
            nr, nc = nr + dr, nc + dc
        if 0 <= nr < len(a) and 0 <= nc < len(a[0]) and a[nr][nc] == b[r][c] and (nr, nc) not in added:
            return True
    return False


def _same_color_on_line(pair: Dict, cell: Cell, bg: int) -> bool:
    a, b = pair["input"], pair["output"]
    r, c = cell
    return any(
        a[fr][fc] == b[r][c] and (fr == r or fc == c or fr - fc == r - c or fr + fc == r + c)
        for fr in range(len(a))
        for fc in range(len(a[0]))
        if a[fr][fc] != bg
    )


def is_colored_line_family(train: List[Dict]) -> bool:
    """Every added cell takes the color of an input cell on its row,
    column or diagonal (lines drawn from or between same-color markers)."""
    for pair in train:
        added = pure_additions(pair)
        if added is None:
            return False
        bg = background_color(pair["input"])
        if not all(_same_color_on_line(pair, cell, bg) for cell in added):
            return False
    return True


def is_ray_family(train: List[Dict]) -> bool:
    """Every added cell continues, in a straight line of added cells,
    into an input cell of the same color."""
    for pair in train:
        added = pure_additions(pair)
        if added is None:
            return False
        added_set = set(added)
        if not all(_has_ray_source(pair, cell, added_set) for cell in added):
            return False
    return True
