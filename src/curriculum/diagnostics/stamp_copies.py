"""Find translated copies of an input object inside the output grid (Round 21)."""
from typing import Dict, List, Set, Tuple

from src.curriculum.diagnostics.stamp_objects import Obj, is_solid_rectangle

Cell = Tuple[int, int]
Copy = Tuple[Cell, str]  # (offset, "exact" | "silhouette")


def _in_bounds(grid, r: int, c: int) -> bool:
    return 0 <= r < len(grid) and 0 <= c < len(grid[0])


def places(obj: Obj, offset: Cell) -> List[Cell]:
    return [(r + offset[0], c + offset[1]) for r, c in obj]


def _mode(inp, out, obj: Obj, offset: Cell, bg: int):
    cells = places(obj, offset)
    if any(not _in_bounds(out, r, c) for r, c in cells):
        return None
    if not any(inp[r][c] != out[r][c] for r, c in cells):
        return None
    if all(out[r][c] == obj[(r - offset[0], c - offset[1])] for r, c in cells):
        return "exact"
    colours = {out[r][c] for r, c in cells}
    return "silhouette" if len(colours) == 1 and bg not in colours else None


def _candidate_offsets(obj: Obj, changed: List[Cell]) -> Set[Cell]:
    return {(q[0] - p[0], q[1] - p[1]) for q in changed for p in obj} - {(0, 0)}


def find_copies(inp, out, obj: Obj, changed: List[Cell], bg: int) -> Dict[Cell, str]:
    """Offsets where the object (exactly, or as a one-colour silhouette) appears in `out`."""
    if len(obj) < 3 or is_solid_rectangle(obj):
        return {}
    found = {}
    for offset in _candidate_offsets(obj, changed):
        mode = _mode(inp, out, obj, offset, bg)
        if mode:
            found[offset] = mode
    return found


def original_kept(out, obj: Obj) -> bool:
    return all(out[r][c] == v for (r, c), v in obj.items())
