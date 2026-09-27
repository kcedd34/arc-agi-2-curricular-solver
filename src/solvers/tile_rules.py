"""Tile/repetition hypothesis detection and application, verified against
100% of a task's train pairs before being trusted (same discipline as
color_mapping.py and crop_rules.py). See ADR 0043.

Only literal tiling is considered: the output is the input repeated
`(row_reps, col_reps)` times with no reflection/alternation, which is
deliberately left to a future symmetry-repair primitive (ADR 0041 item 5)
so the two do not overlap.
"""
from typing import List, NamedTuple, Optional

from src.utils.grid_types import Grid
from src.utils.task_loader import Pair


class TileRepeat(NamedTuple):
    row_reps: int
    col_reps: int


def tile_repeat(grid: Grid, hypothesis: TileRepeat) -> Grid:
    row_reps, col_reps = hypothesis
    tiled_rows = []
    for row in grid:
        tiled_rows.append(row * col_reps)
    return tiled_rows * row_reps


def _repeat_factor(pair: Pair) -> Optional[TileRepeat]:
    ih, iw = len(pair.input), len(pair.input[0])
    oh, ow = len(pair.output), len(pair.output[0])
    if ih == 0 or iw == 0 or oh % ih != 0 or ow % iw != 0:
        return None
    row_reps, col_reps = oh // ih, ow // iw
    if row_reps < 1 or col_reps < 1 or (row_reps, col_reps) == (1, 1):
        return None
    return TileRepeat(row_reps, col_reps)


def detect_tile_hypotheses(pairs: List[Pair]) -> List[TileRepeat]:
    first_factor = _repeat_factor(pairs[0])
    if first_factor is None:
        return []
    if any(_repeat_factor(p) != first_factor for p in pairs[1:]):
        return []
    if all(tile_repeat(p.input, first_factor) == p.output for p in pairs):
        return [first_factor]
    return []


def apply_tile_hypothesis(hypothesis: TileRepeat, grid: Grid) -> Grid:
    return tile_repeat(grid, hypothesis)
