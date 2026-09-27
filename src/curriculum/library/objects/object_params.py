"""Parameter inference for object-pack pieces (staging, RN-CUR-36,
object-pack.md Section 3.5), plus the Section 3.6 inventory-pruning
rows specific to the object pack's own vocabulary (crop layouts,
connectivity/single_color).

Kept separate from `search/params.py`'s generic per-parameter-name
lookup (ADR 0070): the object pack uses the name `color` for two
incompatible things (the recolor/fill_bbox *target* color vs. the
`objects_of_color` *selection* color), which a per-name-only lookup
cannot disambiguate safely. Each function here is named after the piece
it serves instead. Not imported by `search/params.py` or
`search/compose.py` (ADR 0069's staging isolation stays by construction);
intended for Phase 7's `check` runs over staging pieces.
"""
from typing import List, Tuple

from src.curriculum.grid import MAX_COLOR, MIN_COLOR
from src.curriculum.library.objects.object_rearrangement import is_rearrangement_task
from src.curriculum.loader import Task
from src.curriculum.perception.change_inventory import build_task_inventory
from src.curriculum.perception.objects import segment_objects
from src.curriculum.search.pruning import (
    infer_colors_common_to_every_input,
    infer_target_color_candidates,
)

_DIRECTIONS = ("up", "down", "left", "right")
_CONNECTIVITY_SINGLE_COLOR_COMBOS: Tuple[Tuple[int, bool], ...] = (
    (4, True),
    (4, False),
    (8, True),
    (8, False),
)
_DEFAULT_CONNECTIVITY = 4  # matches perception/objects.py::segment_objects' own default


def recolor_target_color_candidates(task: Task) -> List[int]:
    """`recolor_selected`/`fill_bbox_selected`'s `color` (object-pack.md
    Section 3.5 rule 1): reuses `search/pruning.py`'s generic
    added-colors inference, since this is exactly a "target color a
    piece writes into the output" parameter."""
    return infer_target_color_candidates(task)


def objects_of_color_candidates(task: Task) -> List[int]:
    """`objects_of_color`'s `color` (object-pack.md Section 3.5 rule 2):
    reuses `search/pruning.py`'s generic common-to-every-input inference,
    since this is exactly a "selection color" parameter."""
    return infer_colors_common_to_every_input(task)


def background_candidates(task: Task) -> List[int]:
    """`connectivity`/layout's own `background` (the color `Objects()`
    treats as not-an-object, Phase 7 gate check, object-pack.md Section
    5.5) and `erase_selected`/`slide_selected`'s `background` (the color
    an erased/vacated cell is repainted to, i.e. "what the grid's own
    background looks like there") are the same detection role: a color
    missing from even one train input cannot be this task's stable
    background. Rodada 3 (object-pack outer-loop pruning): switched from
    `infer_palette` (union, `search/pruning.py`) to
    `infer_colors_common_to_every_input` (intersection), the same fix
    Rodada 1 already applied to the main library's structurally
    identical `search/params.py::_background_candidates` (ADR 0075) but
    never carried over to this module's own copy (ADR 0070 keeps them
    separate files, not separate rules). Falls back to the full color
    range only in the degenerate case of an empty intersection."""
    common = infer_colors_common_to_every_input(task)
    return common if common else list(range(MIN_COLOR, MAX_COLOR + 1))


def _dominant_object(grid, connectivity: int, single_color: bool):
    objects = segment_objects(grid, connectivity=connectivity, single_color=single_color)
    if len(objects) != 1:
        return None
    return objects[0]


def _direction_from_displacement(d_row: int, d_col: int) -> Tuple[str, ...]:
    """The single direction a pure horizontal-or-vertical displacement
    matches, or every direction when the displacement is diagonal, zero,
    or otherwise not a clean single-axis move."""
    if d_row == 0 and d_col > 0:
        return ("right",)
    if d_row == 0 and d_col < 0:
        return ("left",)
    if d_col == 0 and d_row > 0:
        return ("down",)
    if d_col == 0 and d_row < 0:
        return ("up",)
    return _DIRECTIONS


def slide_direction_candidates(
    task: Task, connectivity: int = _DEFAULT_CONNECTIVITY, single_color: bool = True
) -> List[str]:
    """`slide_selected`'s `direction` (object-pack.md Section 3.5 rule 3):
    all 4 directions, pruned by cross-pair consistency.

    Conservative and narrow in scope: only prunes when every train pair
    has exactly one object in both its input and output grid (so "the
    object" is unambiguous without knowing which selector chose it) and
    every pair's own top-left displacement agrees on the same single
    direction. Any other case (multiple objects, no clean single-axis
    displacement, or pairs disagreeing) falls back to all 4 directions,
    since guessing further would not be conservative."""
    directions_per_pair = []
    for pair in task.train:
        in_obj = _dominant_object(pair.input, connectivity, single_color)
        out_obj = _dominant_object(pair.output, connectivity, single_color)
        if in_obj is None or out_obj is None:
            return list(_DIRECTIONS)
        d_row = out_obj.top - in_obj.top
        d_col = out_obj.left - in_obj.left
        directions_per_pair.append(set(_direction_from_displacement(d_row, d_col)))

    if not directions_per_pair:
        return list(_DIRECTIONS)
    common = directions_per_pair[0]
    for directions in directions_per_pair[1:]:
        common = common & directions
    return sorted(common) if common else list(_DIRECTIONS)


def _object_count_matches(
    task: Task, connectivity: int, single_color: bool
) -> bool:
    return all(
        len(segment_objects(pair.input, connectivity=connectivity, single_color=single_color))
        == len(segment_objects(pair.output, connectivity=connectivity, single_color=single_color))
        for pair in task.train
    )


def connectivity_single_color_candidates(task: Task) -> List[Tuple[int, bool]]:
    """`connectivity`/`single_color` (object-pack.md Section 3.5 rule 4):
    the 4 combinations, pruned to those whose resulting object count
    agrees between a pair's input and output on every train pair. Falls
    back to all 4 when none survives, since the property a piece checks
    (e.g. size, color) may still make an inconsistent-count combination
    the right structural choice for some other reason."""
    if is_rearrangement_task(task):
        return list(_CONNECTIVITY_SINGLE_COLOR_COMBOS)
    valid = [
        combo
        for combo in _CONNECTIVITY_SINGLE_COLOR_COMBOS
        if _object_count_matches(task, combo[0], combo[1])
    ]
    return valid if valid else list(_CONNECTIVITY_SINGLE_COLOR_COMBOS)


def should_include_identity_canvas(task: Task) -> bool:
    """Object-pack.md Section 3.6 `same_shape` row: the identity-canvas
    layout is only structurally plausible when every train pair keeps
    the same shape (it always emits a same-size copy of the input)."""
    return build_task_inventory(task).same_shape


def should_include_crop_layout(task: Task) -> bool:
    """Object-pack.md Section 3.6 `constant_out_shape`/
    `shape_depends_on_content` row: the crop-to-selected-object layout is
    only structurally plausible when the output is not simply a same-
    size copy of the input (`same_shape` already covers that case) and
    either every output shares one fixed shape or the shape genuinely
    depends on which object gets selected."""
    inventory = build_task_inventory(task)
    if inventory.same_shape:
        return False
    return inventory.constant_out_shape or inventory.shape_depends_on_content
