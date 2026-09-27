"""Inference of a 1-to-1 cell-wise color mapping (same shape)."""
from typing import Dict, List, Optional

from src.utils.grid_types import Grid
from src.utils.task_loader import Pair


def same_shape(a: Grid, b: Grid) -> bool:
    return len(a) == len(b) and all(len(ra) == len(rb) for ra, rb in zip(a, b))


def infer_color_mapping(pairs: List[Pair]) -> Optional[Dict[int, int]]:
    mapping: Dict[int, int] = {}
    for pair in pairs:
        if not same_shape(pair.input, pair.output):
            return None
        for in_row, out_row in zip(pair.input, pair.output):
            for in_cell, out_cell in zip(in_row, out_row):
                if in_cell in mapping and mapping[in_cell] != out_cell:
                    return None
                mapping[in_cell] = out_cell
    return mapping


def apply_color_mapping(grid: Grid, mapping: Dict[int, int]) -> Grid:
    return [[mapping.get(cell, cell) for cell in row] for row in grid]
