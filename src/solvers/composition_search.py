"""Depth-2 composition search: applies one primitive from the existing,
already-tested library (grid_ops geometric transforms, color_mapping,
crop_rules, tile_rules), then a second primitive on the result, to test
whether COMBINING primitives solves tasks that none solve alone (ADR
0041/0042/0043: geometry, color mapping, crop and tile each measured
0/40 standalone). See ADR 0044.

Explicitly bounded to depth 2, not the general search engine (ADR 0041
item 6).

Scope decision: stage 1 is restricted to the 8 geometric transforms,
excluding identity. These are the only primitives in this library that
are pure, parameter-free functions of the input grid alone; every other
family (color_mapping, crop_rules, tile_rules) needs to see an
(input, output) pair to fit its parameters, which is not available for
an intermediate stage with no known target. Stage 2 may be any of the
four families, fit against the transformed pairs
`(stage1(input), output)`. Identity is excluded from both stages: as
stage 1 it would just reduce to the already-measured single-primitive
case (all 0/40); as stage 2 it would reduce to a bare geometric
transform, already covered by the 0/54 baseline (ADR 0041).

Same ADR 0038 ambiguity bar as every other primitive in this project: a
composition only counts if it reproduces 100% of a task's train pairs,
and every surviving composition across all (stage1, stage2) choices is
pooled per task; if more than one distinct composition explains the
same data, the task is ambiguous, never resolved by picking one
arbitrarily (see `diagnose_composition_coverage.py`).
"""
from typing import Callable, List, NamedTuple, Optional

from src.solvers.color_mapping import apply_color_mapping, infer_color_mapping
from src.solvers.crop_rules import apply_crop_hypothesis, detect_crop_hypotheses
from src.solvers.tile_rules import apply_tile_hypothesis, detect_tile_hypotheses
from src.utils.grid_ops import GEOMETRIC_TRANSFORMS, identity
from src.utils.grid_types import Grid
from src.utils.task_loader import Pair

_STAGE_TRANSFORMS = [t for t in GEOMETRIC_TRANSFORMS if t is not identity]


class Composition(NamedTuple):
    label: str
    apply: Callable[[Grid], Optional[Grid]]


def _transformed_pairs(pairs: List[Pair], stage1: Callable[[Grid], Grid]) -> List[Pair]:
    return [Pair(input=stage1(p.input), output=p.output) for p in pairs]


def _geometric_stage2(transformed_pairs: List[Pair]):
    found = []
    for stage2 in _STAGE_TRANSFORMS:
        if all(stage2(p.input) == p.output for p in transformed_pairs):
            found.append((f"geometric:{stage2.__name__}", stage2))
    return found


def _color_stage2(transformed_pairs: List[Pair]):
    mapping = infer_color_mapping(transformed_pairs)
    if mapping is None:
        return []
    label = f"color:{sorted(mapping.items())}"
    return [(label, lambda g, m=mapping: apply_color_mapping(g, m))]


def _crop_stage2(transformed_pairs: List[Pair]):
    found = []
    for hypothesis in detect_crop_hypotheses(transformed_pairs):
        found.append((f"crop:{hypothesis}", lambda g, h=hypothesis: apply_crop_hypothesis(h, g)))
    return found


def _tile_stage2(transformed_pairs: List[Pair]):
    found = []
    for hypothesis in detect_tile_hypotheses(transformed_pairs):
        found.append((f"tile:{hypothesis}", lambda g, h=hypothesis: apply_tile_hypothesis(h, g)))
    return found


_STAGE2_GENERATORS = [_geometric_stage2, _color_stage2, _crop_stage2, _tile_stage2]


def _verified_on_all_pairs(composition: Composition, pairs: List[Pair]) -> bool:
    return all(composition.apply(p.input) == p.output for p in pairs)


def find_compositions(pairs: List[Pair]) -> List[Composition]:
    """Every depth-2 composition that reproduces 100% of `pairs`.

    Pool this per task and apply the ADR 0038 ambiguity bar at the call
    site (mirrors `diagnose_crop_tile_coverage.py`): 0 = no candidate,
    1 = solved by composition, >1 = ambiguous.
    """
    compositions = []
    for stage1 in _STAGE_TRANSFORMS:
        transformed_pairs = _transformed_pairs(pairs, stage1)
        for generator in _STAGE2_GENERATORS:
            for stage2_label, stage2_apply in generator(transformed_pairs):
                label = f"{stage1.__name__}->{stage2_label}"
                candidate = Composition(
                    label=label,
                    apply=lambda g, s1=stage1, s2=stage2_apply: s2(s1(g)),
                )
                if _verified_on_all_pairs(candidate, pairs):
                    compositions.append(candidate)
    return compositions
