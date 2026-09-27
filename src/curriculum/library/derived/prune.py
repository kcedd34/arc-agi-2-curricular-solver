"""Inventory pre-filter of the derived family (ADR 0107).

A selection must pick a proper subset of the regions in some train input, and
the cells a train pair changes must fall inside the selected regions. A
parameter source must be able to produce the colours the outputs introduce.
Nothing here decides a candidate is right; it only drops what cannot be."""
from typing import List, Optional, Set

from src.curriculum.library.derived.candidates import CORNER_MEASURE
from src.curriculum.library.derived.facts import PairChange, bbox_cells, task_changes, train_regions
from src.curriculum.library.derived.model import ParamSource, RegionSpec, Selection
from src.curriculum.library.derived.selection_probe import select
from src.curriculum.library.derived.tables import KEY_SETS, learn_color_table
from src.curriculum.loader import Task
from src.curriculum.spec._derive import derive_from_grid
from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._measures import measure_value
from src.curriculum.spec._region_value import RegionValue

Selected = List[List[RegionValue]]


def selected_regions(task: Task, spec: RegionSpec, sel: Optional[Selection]) -> Optional[Selected]:
    """Selected regions per train pair; None when the selection is rejected."""
    regions = train_regions(task, spec)
    if regions is None:
        return None
    if sel is None:
        return regions
    chosen, proper = [], False
    for pair, regs in zip(task.train, regions):
        picked = select(sel, regs, pair.input, spec)
        if picked is None:
            return None
        proper = proper or 0 < len(picked) < len(regs)
        chosen.append(picked)
    return chosen if proper else None


def _corner_cell(region: RegionValue) -> Set:
    return {(region.row0 - 1, region.col0 - 1)}


def covers_changes(task: Task, selected: Selected, with_corner: bool = False) -> bool:
    changes = task_changes(task)
    if not any(change.cells for change in changes):
        return False
    for change, picked in zip(changes, selected):
        allowed: Set = set()
        for region in picked:
            allowed |= bbox_cells(region)
            if with_corner:
                allowed |= _corner_cell(region)
        if not change.cells <= allowed:
            return False
    return True


def _all_new_colors(changes: List[PairChange]) -> Set[int]:
    return set().union(*(change.new_colors for change in changes))


def literal_colors(task: Task, candidates: List[int]) -> List[ParamSource]:
    new = _all_new_colors(task_changes(task))
    return [ParamSource("literal", c) for c in candidates if new == {c}]


def _derived_matches(task: Task, spec: RegionSpec, op: str) -> bool:
    try:
        for pair, change in zip(task.train, task_changes(task)):
            if change.cells and change.new_colors != {derive_from_grid(pair.input, op, spec.background)}:
                return False
    except InterpreterError:
        return False
    return True


def derived_colors(task: Task, spec: RegionSpec, ops) -> List[ParamSource]:
    return [ParamSource("derived", op) for op in ops if _derived_matches(task, spec, op)]


def learned_tables(task: Task, selected: Selected) -> List[ParamSource]:
    observations = [
        (region, pair.input, pair.output) for pair, picked in zip(task.train, selected) for region in picked
    ]
    found = []
    for measures in KEY_SETS:
        table = learn_color_table(observations, measures)
        if table is not None:
            found.append(ParamSource("table", (measures, table)))
    return found


def _cleared_corner_colors(task: Task, selected: Selected) -> Set[int]:
    """Output colours at the corner cells the train pairs actually change."""
    found: Set[int] = set()
    for pair, picked, change in zip(task.train, selected, task_changes(task)):
        for region in picked:
            row, col = next(iter(_corner_cell(region)))
            if (row, col) in change.cells:
                found.add(pair.output[row][col])
    return found


def _marker_colors_explained(task: Task, spec: RegionSpec, selected: Selected) -> bool:
    for pair, picked, change in zip(task.train, selected, task_changes(task)):
        try:
            seen = {measure_value(r, CORNER_MEASURE, pair.input) for r in picked}
        except InterpreterError:
            return False
        if not {c for c in change.new_colors if c != spec.background} <= seen | {0}:
            return False
    return True


def corner_sources(task: Task, spec: RegionSpec, selected: Selected) -> List[ParamSource]:
    """The corner-marker source: regions take the colour of the marker on
    their top-left junction, and the marker cell resets to the one colour the
    train outputs show there."""
    cleared = _cleared_corner_colors(task, selected)
    if len(cleared) != 1 or not _marker_colors_explained(task, spec, selected):
        return []
    return [ParamSource("corner_marker", next(iter(cleared)))]


def erase_fits(task: Task, background: int) -> bool:
    changes = [c for c in task_changes(task) if c.cells]
    return bool(changes) and all(c.new_colors == {background} for c in changes)
