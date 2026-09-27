"""Candidate parameter values for a library primitive, given a task.

Per-parameter-name lookup, not per-primitive: several primitives can
share a parameter name (e.g. "background") and reuse the same candidate
list. RN-CUR-33 step 3: candidates are now hard-pruned from the
demonstrations (`search/pruning.py`) wherever a safe cut exists, not
just ordered with the full range kept as a tail - enumeration only ever
sees combinations the train pairs make plausible. Unknown parameter
names still fall back to the full 0-9 color range so a new primitive
works here with zero changes to this file.
"""
from typing import Any, Dict, List

from src.curriculum.grid import MAX_COLOR, MIN_COLOR
from src.curriculum.loader import Task
from src.curriculum.search.pruning import (
    infer_colors_common_to_every_input,
    infer_consistent_axis_scale,
    infer_target_color_candidates,
)

ALL_COLORS = list(range(MIN_COLOR, MAX_COLOR + 1))


def _background_candidates(task: Task) -> List[int]:
    """`background`'s role wherever it is used (draw_lines_content's/
    isolated_point's stop-scan detection) is "which color counts as
    background", never a color the piece writes - so it is hard-pruned to
    colors present in *every* train-pair input (RN-CUR-33 step 3
    continuation, round-1 pruning package,
    docs/curriculum/rounds/round-1.md): a color missing from even one
    input cannot be the task's stable background, the same conservative
    rule `infer_colors_common_to_every_input` already applies to
    object-pack's `objects_of_color` selection-color parameter. Falls
    back to the full color range only in the degenerate case of an empty
    train set."""
    common = infer_colors_common_to_every_input(task)
    return common if common else list(ALL_COLORS)


def _fill_color_candidates(task: Task) -> List[int]:
    """`fill_content`'s `fill_color`: a color the piece *writes* into the
    output, so it reuses the same added-colors inference already proven
    for object-pack's `recolor_selected`/`fill_bbox_selected` (`search/
    pruning.infer_target_color_candidates`), instead of the full observed
    input palette."""
    return infer_target_color_candidates(task)


MAX_INFERRED_SCALE = 10


def _axis_scale_candidates(task: Task, axis: str) -> List[int]:
    """Hard-pruned to the single per-axis tile-scale factor the train
    pairs agree on (`search/pruning.infer_consistent_axis_scale`), rows
    and columns inferred independently so a non-square block-tile rule
    (e.g. a 2x3 grid) is still expressible. Only falls back to the full
    `1..MAX_INFERRED_SCALE` range when the train pairs disagree or the
    ratio isn't a whole number - search/rank.py's own train-pair
    verification still rejects every wrong guess in that fallback case.
    """
    consistent = infer_consistent_axis_scale(task, axis)
    if consistent is not None:
        return [consistent]
    return list(range(1, MAX_INFERRED_SCALE + 1))


def _scale_rows_candidates(task: Task) -> List[int]:
    return _axis_scale_candidates(task, "row")


def _scale_cols_candidates(task: Task) -> List[int]:
    return _axis_scale_candidates(task, "col")


_AXIS_CANDIDATES = ["horizontal", "vertical"]


def _axis_candidates(task: Task) -> List[str]:
    return list(_AXIS_CANDIDATES)


_STOP_CONDITION_CANDIDATES = ["same_color_isolated", "border", "any_obstacle"]


def _stop_condition_candidates(task: Task) -> List[str]:
    """All 3 `SegmentTo` stop conditions (task 4, ADR 0068): not
    prunable from the train pairs the way background/scale are, so the
    search tries all 3 and lets train-pair verification pick the one that
    actually matches (`draw_lines` content piece)."""
    return list(_STOP_CONDITION_CANDIDATES)


_CANDIDATE_BUILDERS = {
    "background": _background_candidates,
    "fill_color": _fill_color_candidates,
    "scale_rows": _scale_rows_candidates,
    "scale_cols": _scale_cols_candidates,
    "axis": _axis_candidates,
    "stop_condition": _stop_condition_candidates,
}


def candidates_for_param(param_name: str, task: Task) -> List[Any]:
    builder = _CANDIDATE_BUILDERS.get(param_name)
    if builder is not None:
        return builder(task)
    return list(ALL_COLORS)


def candidates_for_primitive(params: List[str], task: Task) -> Dict[str, List[Any]]:
    return {name: candidates_for_param(name, task) for name in params}
