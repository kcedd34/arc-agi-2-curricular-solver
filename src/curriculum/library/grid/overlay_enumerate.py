"""Candidate enumeration for the overlay grid pack (ADR 0094). Train pairs
only: the split shape must be the same for every pair and explain each
output's size; the mask table is learned from the train outputs."""
from typing import Dict, Iterator, List, Optional, Tuple

from src.curriculum.grid import Grid
from src.curriculum.library.grid.overlay_composition import MaskTable, OverlayComposition
from src.curriculum.library.objects.object_params import background_candidates
from src.curriculum.loader import Task

MAX_PARTS = 4
MIN_PART_CELLS = 2


def _count_along(total: int, part: int, divider: bool) -> Optional[int]:
    gap = 1 if divider else 0
    if (total + gap) % (part + gap):
        return None
    return (total + gap) // (part + gap)


def split_shapes(task: Task) -> List[Tuple[int, int, bool]]:
    """`(n_rows, n_cols, divider)` splits that explain every train pair."""
    shapes = []
    for divider in (False, True):
        counts = {
            (_count_along(len(p.input), len(p.output), divider), _count_along(len(p.input[0]), len(p.output[0]), divider))
            for p in task.train
        }
        if len(counts) != 1:
            continue
        n_rows, n_cols = next(iter(counts))
        if n_rows and n_cols and 2 <= n_rows * n_cols <= MAX_PARTS:
            shapes.append((n_rows, n_cols, divider))
    return shapes


def _part_origins(n_rows: int, n_cols: int, divider: bool, height: int, width: int) -> List[Tuple[int, int]]:
    gap = 1 if divider else 0
    return [(r * (height + gap), c * (width + gap)) for r in range(n_rows) for c in range(n_cols)]


def _pair_masks(pair, shape, background: int):
    n_rows, n_cols, divider = shape
    height, width = len(pair.output), len(pair.output[0])
    origins = _part_origins(n_rows, n_cols, divider, height, width)
    for r in range(height):
        for c in range(width):
            mask = tuple(pair.input[r0 + r][c0 + c] != background for r0, c0 in origins)
            yield mask, pair.output[r][c]


def learn_table(task: Task, shape: Tuple[int, int, bool], background: int) -> Optional[MaskTable]:
    """Mask -> output color, or None on a conflict or a degenerate table."""
    table: Dict[Tuple[bool, ...], int] = {}
    for pair in task.train:
        for mask, color in _pair_masks(pair, shape, background):
            if table.setdefault(mask, color) != color:
                return None
    if len(set(table.values())) < 2:
        return None
    return tuple(sorted(table.items()))


def enumerate_overlay_compositions(task: Task) -> Iterator[OverlayComposition]:
    for shape in split_shapes(task):
        if any(len(p.output) * len(p.output[0]) < MIN_PART_CELLS for p in task.train):
            continue
        for background in background_candidates(task):
            table = learn_table(task, shape, background)
            if table is not None:
                yield OverlayComposition(shape[0], shape[1], shape[2], background, table)
