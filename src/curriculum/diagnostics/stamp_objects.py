"""Object extraction for the stamp signature sweep (Round 21). Train pairs only."""
from typing import Dict, List, Tuple

Cell = Tuple[int, int]
Obj = Dict[Cell, int]

_N8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


def _flood(grid, bg: int, start: Cell, seen: set) -> Obj:
    stack, obj = [start], {}
    seen.add(start)
    while stack:
        r, c = stack.pop()
        obj[(r, c)] = grid[r][c]
        for dr, dc in _N8:
            n = (r + dr, c + dc)
            if 0 <= n[0] < len(grid) and 0 <= n[1] < len(grid[0]) and n not in seen and grid[n[0]][n[1]] != bg:
                seen.add(n)
                stack.append(n)
    return obj


def components(grid, bg: int) -> List[Obj]:
    """Multicolour 8-connected components of non-background cells."""
    seen: set = set()
    found = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != bg and (r, c) not in seen:
                found.append(_flood(grid, bg, (r, c), seen))
    return found


def is_solid_rectangle(obj: Obj) -> bool:
    rows = [r for r, _ in obj]
    cols = [c for _, c in obj]
    area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
    return area == len(obj) and len(set(obj.values())) == 1
