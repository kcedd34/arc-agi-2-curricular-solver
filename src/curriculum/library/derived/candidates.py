"""Candidate axes of the derived family (ADR 0107): the selections a region
kind offers, and the actions with their parameter sources."""
from typing import List, Tuple

from src.curriculum.library.derived.model import Selection, ValueRule
from src.curriculum.library.derived.tables import KEY_SETS

OBJECT_MEASURES = ("size", "width", "height", "hole_cells", "colors", "border_distance")
SEGMENT_MEASURES = ("gap",)
TOTAL_MEASURES = ("hole_cells", "size", "width", "height", "colors")
COLOR_OPS = ("rarest_color", "common_color")
MODES = ("min", "max")

OBJECT_ACTIONS = (
    "erase_selected",
    "recolor_selected",
    "fill_bbox_selected",
    "recolor_border_selected",
    "recolor_interior_selected",
    "fill_holes_selected",
)
CORNER_ACTIONS = ("recolor_clear_corner_nw",)
FLAG_MEASURES = ("closed", "multi_cell")
CORNER_MEASURE = "corner_nw_color"
SEGMENT_ACTIONS = ("fill_between",)
NO_COLOR_ACTIONS = ("erase_selected",)


def actions_for(kind: str) -> Tuple[str, ...]:
    return SEGMENT_ACTIONS if kind != "objects" else OBJECT_ACTIONS + CORNER_ACTIONS


def extremum_selections(kind: str) -> List[Selection]:
    measures = OBJECT_MEASURES if kind == "objects" else SEGMENT_MEASURES
    return [Selection(m, ValueRule(mode)) for m in measures for mode in MODES]


def total_selections(kind: str) -> List[Selection]:
    if kind != "objects":
        return []
    return [Selection(m, ValueRule("total", "count_color", op)) for m in TOTAL_MEASURES for op in COLOR_OPS]


def flag_selections(kind: str) -> List[Selection]:
    if kind != "objects":
        return []
    return [Selection(m, ValueRule("equals", literal=v)) for m in FLAG_MEASURES for v in (0, 1)]


def all_selections(kind: str) -> List[Selection]:
    return extremum_selections(kind) + total_selections(kind) + flag_selections(kind)


def param_source_count(kind: str, n_literals: int) -> int:
    """Unpruned parameter sources of one colour-taking action."""
    element = 1 if kind != "objects" else 0
    return n_literals + len(COLOR_OPS) + element + len(KEY_SETS)


def action_source_count(kind: str, name: str, n_literals: int) -> int:
    if name in NO_COLOR_ACTIONS or name in CORNER_ACTIONS:
        return 1
    return param_source_count(kind, n_literals)
