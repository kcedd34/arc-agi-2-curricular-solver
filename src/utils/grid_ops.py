"""Geometric grid transformation primitives."""
from typing import Callable

from src.utils.grid_types import Grid

Transform = Callable[[Grid], Grid]


def identity(grid: Grid) -> Grid:
    return [row[:] for row in grid]


def rotate90(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid[::-1])]


def rotate180(grid: Grid) -> Grid:
    return [row[::-1] for row in grid[::-1]]


def rotate270(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid)][::-1]


def flip_horizontal(grid: Grid) -> Grid:
    return [row[::-1] for row in grid]


def flip_vertical(grid: Grid) -> Grid:
    return grid[::-1]


def transpose(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid)]


def anti_transpose(grid: Grid) -> Grid:
    """Reflection across the anti-diagonal, the 8th element of the D4
    dihedral group (identity/rotate90/180/270 plus the 4 reflections),
    completing the set the 7 transforms above were one short of."""
    return rotate180(transpose(grid))


GEOMETRIC_TRANSFORMS = [
    identity,
    rotate90,
    rotate180,
    rotate270,
    flip_horizontal,
    flip_vertical,
    transpose,
    anti_transpose,
]
