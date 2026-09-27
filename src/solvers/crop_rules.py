"""Crop hypothesis detection and application, verified against 100% of a
task's train pairs before ever being trusted (same discipline as
color_mapping.py and the ADR 0025/0038 shape rules). See ADR 0043.

Two independent hypothesis families are tested:
- FixedWindowCrop: a constant (row, col, height, width) window, found by
  exhaustive search on the first train pair and confirmed on the rest.
- BoundingBoxCrop: the tightest box containing all non-background cells,
  under one of two background policies (fixed color 0, or the grid's own
  most common color).

`detect_crop_hypotheses` returns every hypothesis that fits ALL train
pairs; more than one surviving hypothesis means the data is ambiguous
between rules and neither should be trusted on unseen input.
"""
from typing import List, NamedTuple, Optional, Tuple, Union

from src.utils.grid_types import Grid
from src.utils.task_loader import Pair


class FixedWindowCrop(NamedTuple):
    row: int
    col: int
    height: int
    width: int


class BoundingBoxCrop(NamedTuple):
    background: str  # "zero" or "most_common"


CropHypothesis = Union[FixedWindowCrop, BoundingBoxCrop]


def crop_fixed_window(grid: Grid, hypothesis: FixedWindowCrop) -> Optional[Grid]:
    r, c, h, w = hypothesis
    if r < 0 or c < 0 or r + h > len(grid) or c + w > len(grid[0]):
        return None
    return [row[c:c + w] for row in grid[r:r + h]]


def detect_fixed_window_hypotheses(pairs: List[Pair]) -> List[FixedWindowCrop]:
    first = pairs[0]
    ih, iw = len(first.input), len(first.input[0])
    oh, ow = len(first.output), len(first.output[0])
    if oh > ih or ow > iw or (oh, ow) == (ih, iw):
        return []
    candidates = []
    for r in range(ih - oh + 1):
        for c in range(iw - ow + 1):
            window = FixedWindowCrop(r, c, oh, ow)
            if all(crop_fixed_window(p.input, window) == p.output for p in pairs):
                candidates.append(window)
    return candidates


def _most_common_color(grid: Grid) -> int:
    counts = {}
    for row in grid:
        for cell in row:
            counts[cell] = counts.get(cell, 0) + 1
    return max(counts, key=counts.get)


def _background_color(grid: Grid, background: str) -> int:
    return 0 if background == "zero" else _most_common_color(grid)


def _bounding_box(grid: Grid, background: str) -> Optional[Tuple[int, int, int, int]]:
    bg = _background_color(grid, background)
    content_rows = [r for r, row in enumerate(grid) if any(cell != bg for cell in row)]
    if not content_rows:
        return None
    content_cols = [c for c in range(len(grid[0])) if any(row[c] != bg for row in grid)]
    return min(content_rows), min(content_cols), max(content_rows), max(content_cols)


def crop_bounding_box(grid: Grid, background: str) -> Optional[Grid]:
    box = _bounding_box(grid, background)
    if box is None:
        return None
    r0, c0, r1, c1 = box
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def _actually_crops_at_least_once(pairs: List[Pair], background: str) -> bool:
    return any(
        _bounding_box(p.input, background) != (0, 0, len(p.input) - 1, len(p.input[0]) - 1)
        for p in pairs
    )


def detect_bounding_box_hypotheses(pairs: List[Pair]) -> List[BoundingBoxCrop]:
    hypotheses = []
    for background in ("zero", "most_common"):
        if not _actually_crops_at_least_once(pairs, background):
            continue
        if all(crop_bounding_box(p.input, background) == p.output for p in pairs):
            hypotheses.append(BoundingBoxCrop(background))
    return hypotheses


def detect_crop_hypotheses(pairs: List[Pair]) -> List[CropHypothesis]:
    return detect_fixed_window_hypotheses(pairs) + detect_bounding_box_hypotheses(pairs)


def apply_crop_hypothesis(hypothesis: CropHypothesis, grid: Grid) -> Optional[Grid]:
    if isinstance(hypothesis, FixedWindowCrop):
        return crop_fixed_window(grid, hypothesis)
    if isinstance(hypothesis, BoundingBoxCrop):
        return crop_bounding_box(grid, hypothesis.background)
    raise TypeError(f"unknown crop hypothesis type: {type(hypothesis)}")
