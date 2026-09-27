"""Candidate enumeration of the derived family (ADR 0107): region kind x
selection x action x parameter source, pruned by the task inventory before
anything is verified. Reports the hypothesis count before and after."""
from typing import Iterator, List, NamedTuple, Optional, Tuple

from src.curriculum.library.derived import candidates as cand
from src.curriculum.library.derived import prune
from src.curriculum.library.derived.model import Action, DerivedComposition, ParamSource, RegionSpec, Selection
from src.curriculum.library.derived.regions import region_specs
from src.curriculum.library.derived.shift_enumerate import shift_compositions, shift_unpruned
from src.curriculum.library.derived.slide_enumerate import slide_compositions, slide_unpruned
from src.curriculum.library.derived.stamp_enumerate import stamp_compositions, stamp_specs, stamp_unpruned
from src.curriculum.library.objects._task_cache import cached_for_task
from src.curriculum.library.objects.object_params import recolor_target_color_candidates
from src.curriculum.loader import Task


class HypothesisCounts(NamedTuple):
    before: int
    after: int


def _sources(task: Task, spec: RegionSpec, name: str, selected: prune.Selected) -> List[Optional[ParamSource]]:
    if name in cand.NO_COLOR_ACTIONS:
        return [None] if prune.erase_fits(task, spec.background) else []
    if name in cand.CORNER_ACTIONS:
        return prune.corner_sources(task, spec, selected)
    sources = prune.literal_colors(task, recolor_target_color_candidates(task))
    sources += prune.derived_colors(task, spec, cand.COLOR_OPS)
    if spec.kind != "objects":
        sources.append(ParamSource("element", "color"))
    return sources + prune.learned_tables(task, selected)


def _for_selection(task: Task, spec: RegionSpec, sel: Optional[Selection]) -> List[DerivedComposition]:
    selected = prune.selected_regions(task, spec, sel)
    if selected is None:
        return []
    found = []
    for name in cand.actions_for(spec.kind):
        if not prune.covers_changes(task, selected, name in cand.CORNER_ACTIONS):
            continue
        for source in _sources(task, spec, name, selected):
            found.append(DerivedComposition(spec, (Action(name, source, sel),)))
    return found


def _unpruned(task: Task, spec: RegionSpec) -> int:
    n_literals = len(recolor_target_color_candidates(task))
    per_selection = sum(
        cand.action_source_count(spec.kind, name, n_literals) for name in cand.actions_for(spec.kind)
    )
    return (1 + len(cand.all_selections(spec.kind))) * per_selection


def _generated(task: Task, spec: RegionSpec, base: List[Selection]) -> List[Selection]:
    from src.curriculum.discovery.switch import generated_enabled

    if not generated_enabled():
        return []
    from src.curriculum.discovery.task_generated import generated_selections

    return generated_selections(task, spec, base)


def _walk(task: Task) -> Tuple[List[DerivedComposition], int]:
    survivors: List[DerivedComposition] = []
    before = 0
    for spec in region_specs(task):
        before += _unpruned(task, spec) + slide_unpruned(task, spec) + shift_unpruned(spec)
        base = cand.all_selections(spec.kind)
        for sel in [None] + base + _generated(task, spec, base):
            survivors += _for_selection(task, spec, sel)
        survivors += slide_compositions(task, spec) + shift_compositions(task, spec)
    for spec in stamp_specs(task):
        before += stamp_unpruned(spec)
        survivors += stamp_compositions(task, spec)
    return survivors, before


def _walked(task: Task) -> Tuple[List[DerivedComposition], int]:
    from src.curriculum.discovery.switch import walk_cache_key

    return cached_for_task(task, walk_cache_key(), lambda: _walk(task))


def enumerate_derived_compositions(task: Task) -> Iterator[DerivedComposition]:
    return iter(_walked(task)[0])


def derived_hypothesis_counts(task: Task) -> HypothesisCounts:
    survivors, before = _walked(task)
    return HypothesisCounts(before, len(survivors))
