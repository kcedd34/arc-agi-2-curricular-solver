"""Slide-toward compositions of the derived family (ADR 0107): movers and
targets are selected by colour, optionally the extreme mover advances one
more step, optionally the targets are recoloured. Pruned by a probe that
every train input has both groups and that distances vary somewhere."""
from typing import List, Optional, Tuple

from src.curriculum.library.derived.model import (
    Action,
    DerivedComposition,
    ParamSource,
    RegionSpec,
    Selection,
    ValueRule,
)
from src.curriculum.library.derived.facts import train_regions
from src.curriculum.library.derived.selection_probe import select
from src.curriculum.library.objects.object_params import objects_of_color_candidates, recolor_target_color_candidates
from src.curriculum.loader import Task
from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._measures import measure_value

SLIDE = "slide_toward"
EXTRAS = (None, "min", "max")


def color_selection(color: int) -> Selection:
    return Selection("color", ValueRule("equals", literal=color))


def _color_pairs(task: Task, spec: RegionSpec) -> List[Tuple[int, int]]:
    colors = [c for c in objects_of_color_candidates(task) if c != spec.background]
    return [(target, mover) for target in colors for mover in colors if target != mover]


def _distances(regions, grid, spec: RegionSpec, target: int, mover: int) -> Optional[List[int]]:
    targets = select(color_selection(target), regions, grid, spec)
    movers = select(color_selection(mover), regions, grid, spec)
    if not targets or not movers:
        return None
    try:
        return [measure_value(m, "distance_to", targets) for m in movers]
    except (InterpreterError, ValueError, KeyError):
        return None


def _probe(task: Task, spec: RegionSpec, per_pair, target: int, mover: int) -> bool:
    varies = False
    for pair, regions in zip(task.train, per_pair):
        distances = _distances(regions, pair.input, spec, target, mover)
        if not distances:
            return False
        varies = varies or len(set(distances)) > 1
    return varies


def _actions(target: int, mover: int, recolor: Optional[int], extra: Optional[str]) -> Tuple[Action, ...]:
    slide = Action(
        SLIDE, None, color_selection(mover), color_selection(target),
        Selection("distance_to", ValueRule(extra)) if extra else None,
    )
    if recolor is None:
        return (slide,)
    return (Action("recolor_selected", ParamSource("literal", recolor), color_selection(target)), slide)


def _variants(task: Task) -> List[Tuple[Optional[int], Optional[str]]]:
    recolors: List[Optional[int]] = [None] + list(recolor_target_color_candidates(task))
    return [(recolor, extra) for recolor in recolors for extra in EXTRAS]


def slide_unpruned(task: Task, spec: RegionSpec) -> int:
    if spec.kind != "objects" or not spec.single_color:
        return 0
    return len(_color_pairs(task, spec)) * len(_variants(task))


def slide_compositions(task: Task, spec: RegionSpec) -> List[DerivedComposition]:
    per_pair = train_regions(task, spec) if slide_unpruned(task, spec) else None
    if per_pair is None:
        return []
    found = []
    for target, mover in _color_pairs(task, spec):
        if _probe(task, spec, per_pair, target, mover):
            found += [DerivedComposition(spec, _actions(target, mover, r, e)) for r, e in _variants(task)]
    return found
