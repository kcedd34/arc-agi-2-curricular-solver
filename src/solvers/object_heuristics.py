"""Cheap connected-component heuristics for object-level extraction,
tested against train pairs only, before committing to a full
object-level primitive build (ADR 0041 item 4). See ADR 0045.

Three selection rules x two background policies x two connectivities
= 12 candidate variants, each a pure function of the input grid alone:
- largest: the component with the most cells.
- rarest_color: the component whose color is the least frequent color
  in the whole grid.
- most_frequent_shape: the component whose normalized shape (its cells'
  offsets relative to its own bounding box) recurs most often among all
  components in the grid.

Every variant crops to the selected component's bounding box and keeps
the grid's original values inside that box, rather than masking
everything outside the component to background - a deliberate scope
choice (ADR 0045), mirroring crop_rules.BoundingBoxCrop's background
policy design rather than a full segmentation mask.

A variant only counts as a candidate for a task if it reproduces 100%
of the task's train pairs; `detect_object_heuristics` pools all
surviving variants. Ambiguity (>1 survivor) is the caller's job to
check, same ADR 0038 bar as every other primitive in this project.
"""
from collections import Counter
from typing import FrozenSet, List, NamedTuple, Optional, Tuple

from src.solvers.connected_components import (
    Component,
    bounding_box,
    crop_to_bbox,
    find_color_components,
)
from src.utils.grid_types import Grid
from src.utils.task_loader import Pair


class ObjectHeuristic(NamedTuple):
    background: str  # "zero" or "most_common"
    connectivity: int  # 4 or 8
    selection: str  # "largest", "rarest_color", "most_frequent_shape"


def _most_common_color(grid: Grid) -> int:
    counts = Counter(cell for row in grid for cell in row)
    return counts.most_common(1)[0][0]


def _background_color(grid: Grid, background: str) -> int:
    return 0 if background == "zero" else _most_common_color(grid)


def _normalized_shape(cells) -> FrozenSet[Tuple[int, int]]:
    r0, c0, _, _ = bounding_box(cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _select_component(components: List[Component], grid: Grid, selection: str) -> Optional[Component]:
    if not components:
        return None
    if selection == "largest":
        return max(components, key=lambda comp: len(comp.cells))
    if selection == "rarest_color":
        color_counts = Counter(cell for row in grid for cell in row)
        return min(components, key=lambda comp: color_counts[comp.color])
    if selection == "most_frequent_shape":
        shape_counts = Counter(_normalized_shape(comp.cells) for comp in components)
        return max(components, key=lambda comp: shape_counts[_normalized_shape(comp.cells)])
    raise ValueError(f"unknown selection: {selection}")


def apply_object_heuristic(heuristic: ObjectHeuristic, grid: Grid) -> Optional[Grid]:
    background = _background_color(grid, heuristic.background)
    components = find_color_components(grid, heuristic.connectivity, background)
    selected = _select_component(components, grid, heuristic.selection)
    if selected is None:
        return None
    return crop_to_bbox(grid, bounding_box(selected.cells))


_BACKGROUNDS = ("zero", "most_common")
_CONNECTIVITIES = (4, 8)
_SELECTIONS = ("largest", "rarest_color", "most_frequent_shape")


def all_object_heuristics() -> List[ObjectHeuristic]:
    return [
        ObjectHeuristic(background, connectivity, selection)
        for background in _BACKGROUNDS
        for connectivity in _CONNECTIVITIES
        for selection in _SELECTIONS
    ]


def detect_object_heuristics(pairs: List[Pair]) -> List[ObjectHeuristic]:
    return [
        heuristic
        for heuristic in all_object_heuristics()
        if all(apply_object_heuristic(heuristic, p.input) == p.output for p in pairs)
    ]
