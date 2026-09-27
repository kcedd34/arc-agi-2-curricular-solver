"""Shift compositions of the derived family (ADR 0107): every region moves by
a (dr, dc) read from a table keyed by one of its measures."""
from typing import List

from src.curriculum.library.derived.facts import train_regions
from src.curriculum.library.derived.model import Action, DerivedComposition, ParamSource, RegionSpec
from src.curriculum.library.derived.shift_tables import SHIFT_KEY_SETS, learn_shift_table
from src.curriculum.loader import Task

TRANSLATE = "translate_selected"


def shift_unpruned(spec: RegionSpec) -> int:
    return len(SHIFT_KEY_SETS) if spec.kind == "objects" and spec.single_color else 0


def shift_compositions(task: Task, spec: RegionSpec) -> List[DerivedComposition]:
    per_pair = train_regions(task, spec) if shift_unpruned(spec) else None
    if per_pair is None:
        return []
    observations = [(region, pair.output) for pair, regions in zip(task.train, per_pair) for region in regions]
    found = []
    for measures in SHIFT_KEY_SETS:
        table = learn_shift_table(observations, measures)
        if table is not None:
            found.append(DerivedComposition(spec, (Action(TRANSLATE, ParamSource("shift", (measures, table)), None),)))
    return found
