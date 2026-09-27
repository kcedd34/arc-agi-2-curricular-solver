"""Movement signatures (ADR 0093). Train pairs only (RN-CUR-03/05)."""
from typing import Dict, List

from src.curriculum.tag_signatures import background_color

Grid = List[List[int]]


def _fall_line(line: List[int], bg: int) -> List[int]:
    kept = [v for v in line if v != bg]
    return [bg] * (len(line) - len(kept)) + kept


def _gravity_down(g: Grid) -> Grid:
    bg = background_color(g)
    cols = [_fall_line([row[c] for row in g], bg) for c in range(len(g[0]))]
    return [[cols[c][r] for c in range(len(g[0]))] for r in range(len(g))]


def _rot90(g: Grid) -> Grid:
    return [list(row) for row in zip(*g[::-1])]


def _gravity(g: Grid, quarter_turns: int) -> Grid:
    """Cell-wise gravity toward the side reached by `quarter_turns`."""
    turned = g
    for _ in range(quarter_turns):
        turned = _rot90(turned)
    fallen = _gravity_down(turned)
    for _ in range((4 - quarter_turns) % 4):
        fallen = _rot90(fallen)
    return fallen


def is_cell_gravity_family(train: List[Dict]) -> bool:
    """Some one of the four directions makes every output equal to the
    cell-wise gravity of its input."""
    return any(all(_gravity(p["input"], q) == p["output"] for p in train) for q in range(4))
