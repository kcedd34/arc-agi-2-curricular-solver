"""Compact text rendering of grids and demonstration pairs (background as a dot)."""
from typing import List, Sequence

Grid = Sequence[Sequence[int]]
PAIR_GAP = "   "


def render_row(row: Sequence[int]) -> str:
    return "".join("." if value == 0 else str(value) for value in row)


def render_grid(grid: Grid) -> List[str]:
    return [render_row(row) for row in grid]


def render_pair(index: int, source: Grid, target: Grid) -> str:
    left, right = render_grid(source), render_grid(target)
    width = max(len(line) for line in left)
    height = max(len(left), len(right))
    left += [""] * (height - len(left))
    right += [""] * (height - len(right))
    body = [f"{a.ljust(width)}{PAIR_GAP}{b}".rstrip() for a, b in zip(left, right)]
    return "\n".join([f"Example {index}: input | output"] + body)


def render_examples(pairs: Sequence[tuple]) -> str:
    return "\n\n".join(render_pair(i, a, b) for i, (a, b) in enumerate(pairs, start=1))
