"""Tiny grid builders shared by the derived-family tests."""
from typing import Dict, List, Tuple

Cells = List[Tuple[int, int]]


def blank(rows: int, cols: int, fill: int = 0) -> List[List[int]]:
    return [[fill] * cols for _ in range(rows)]


def paint(grid: List[List[int]], color: int, cells: Cells) -> List[List[int]]:
    out = [row[:] for row in grid]
    for r, c in cells:
        out[r][c] = color
    return out


def with_objects(rows: int, cols: int, objects: Dict[int, List[Cells]], fill: int = 0):
    grid = blank(rows, cols, fill)
    for color, shapes in objects.items():
        for cells in shapes:
            grid = paint(grid, color, cells)
    return grid


def hbar(row: int, col: int, length: int) -> Cells:
    return [(row, col + i) for i in range(length)]
