"""Stamp compositions of the derived family (ADR 0109): templates and anchors
are two proper selections of the same regions; the template is copied onto
each anchor with the offset that pins its key cell (or bbox origin) there.
Pruned by requiring both groups in every train input, disjoint, and the
pure-Python prediction to reproduce every train output."""
from itertools import product
from typing import Dict, List, Optional, Tuple

from src.curriculum.grid import grid_dims
from src.curriculum.library.derived import candidates as cand
from src.curriculum.library.derived.facts import task_changes, train_regions
from src.curriculum.library.derived.lowering_stamp import ALIGNS, ERASES, PAIRINGS
from src.curriculum.library.derived.regions import region_specs
from src.curriculum.library.derived.model import Action, DerivedComposition, ParamSource, RegionSpec, Selection
from src.curriculum.library.derived.selection_probe import select
from src.curriculum.library.derived.stamp_predict import predict_stamp
from src.curriculum.loader import Task
from src.curriculum.spec._region_value import RegionValue

STAMP = "stamp"
OPTIONS = tuple(product(ALIGNS, PAIRINGS, ERASES))
MAX_REGIONS = 48  # beyond this the selection probes dominate the enumeration time
Picked = List[List[RegionValue]]


def stamp_specs(task: Task) -> List[RegionSpec]:
    """The task's region specs plus the multicolour object partitions a stamp
    template needs, which the count-consistency prune of `region_specs` drops."""
    specs = region_specs(task)
    backgrounds = sorted({spec.background for spec in specs})
    extra = [RegionSpec("objects", conn, False, bg) for bg in backgrounds for conn in (4, 8)]
    return specs + [spec for spec in extra if spec not in specs]


def stamp_unpruned(spec: RegionSpec) -> int:
    if spec.kind != "objects":
        return 0
    return len(cand.all_selections(spec.kind)) ** 2 * len(OPTIONS)


def _same_shape(task: Task) -> bool:
    return all(grid_dims(p.input) == grid_dims(p.output) for p in task.train)


def _groups(task: Task, spec: RegionSpec, per_pair) -> Dict[Selection, Picked]:
    """Selections that pick a non-empty proper subset in every train input."""
    groups = {}
    for sel in cand.all_selections(spec.kind):
        picked = [select(sel, regions, pair.input, spec) for pair, regions in zip(task.train, per_pair)]
        if all(p and len(p) < len(regs) for p, regs in zip(picked, per_pair)):
            groups[sel] = picked
    return groups


def _disjoint(templates: Picked, anchors: Picked) -> bool:
    return all(not ({id(r) for r in t} & {id(r) for r in a}) for t, a in zip(templates, anchors))


def _reproduces(task: Task, spec: RegionSpec, per_pair, templates: Picked, anchors: Picked, options) -> bool:
    for pair, regions, tpl, anc in zip(task.train, per_pair, templates, anchors):
        if predict_stamp(pair.input, regions, tpl, anc, options, spec.background) != pair.output:
            return False
    return True


def _pairs(groups: Dict[Selection, Picked]) -> List[Tuple[Selection, Selection]]:
    return [(t, a) for t, a in product(groups, groups) if t != a and _disjoint(groups[t], groups[a])]


def stamp_compositions(task: Task, spec: RegionSpec) -> List[DerivedComposition]:
    per_pair = train_regions(task, spec) if stamp_unpruned(spec) and _same_shape(task) else None
    if per_pair is None or any(len(regions) > MAX_REGIONS for regions in per_pair):
        return []
    if not any(change.cells for change in task_changes(task)):
        return []
    groups = _groups(task, spec, per_pair)
    found = []
    for tpl_sel, anc_sel in _pairs(groups):
        for options in OPTIONS:
            if _reproduces(task, spec, per_pair, groups[tpl_sel], groups[anc_sel], options):
                action = Action(STAMP, ParamSource(STAMP, options), tpl_sel, anc_sel)
                found.append(DerivedComposition(spec, (action,)))
    return found
