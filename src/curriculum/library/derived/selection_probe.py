"""Applies a `Selection` to concrete regions with the interpreter's own
measures and derivations (ADR 0107), for the inventory prune."""
from typing import List, Optional

from src.curriculum.grid import Grid
from src.curriculum.library.derived.model import RegionSpec, Selection
from src.curriculum.spec._derive import derive_from_grid, derive_from_regions
from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._measures import GRID_ARG_MEASURES, measure_value
from src.curriculum.spec._region_value import RegionValue


def _rule_target(sel: Selection, regions: List[RegionValue], grid: Grid, spec: RegionSpec) -> int:
    rule = sel.rule
    if rule.op == "equals":
        return rule.literal
    if rule.op == "total":
        arg = derive_from_grid(grid, rule.color_op, spec.background) if rule.color_op else 0
        return derive_from_regions(regions, "total", rule.over, arg)
    return derive_from_regions(regions, rule.op, sel.measure, grid if sel.measure in GRID_ARG_MEASURES else 0)


def select(sel: Selection, regions: List[RegionValue], grid: Grid, spec: RegionSpec) -> Optional[List[RegionValue]]:
    """The selected regions, or None when the rule has no answer here."""
    try:
        target = _rule_target(sel, regions, grid, spec)
        arg = grid if sel.measure in GRID_ARG_MEASURES else 0
        return [r for r in regions if measure_value(r, sel.measure, arg) == target]
    except (InterpreterError, ValueError, KeyError):
        return None
