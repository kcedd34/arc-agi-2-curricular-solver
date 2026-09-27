"""Augmentation robustness filter (ADR 0110, corrected by ADR 0111): a hit must
reproduce every train output on the task rotated, mirrored and (when literal
colours are the only colour parameters) colour-permuted, with the composition's
literal colours mapped through the same permutation. A transform is only
demanded when the demonstrations are provably invariant under it (each
transformed pair is already a demonstration pair); otherwise the filter does
not apply to that transform, since orientation or colour may be part of the rule."""
from typing import Callable, Dict, List, NamedTuple

from src.curriculum.discovery.augment import GEOMETRIC, color_permutation, permuted_task, transformed_task
from src.curriculum.library.derived.lowering import build_derived_steps
from src.curriculum.library.derived.model import Action, DerivedComposition, ParamSource
from src.curriculum.grid import Grid
from src.curriculum.loader import Task

_TABLE_KINDS = ("table", "corner_marker", "shift")
_AXIS_SWAPS = ("rot90", "rot270", "transpose", "anti_transpose")
_KIND_SWAP = {"row_segments": "col_segments", "col_segments": "row_segments"}


class Equivariance(NamedTuple):
    passed: bool
    failed: List[str]


def _matches(composition: DerivedComposition, task: Task) -> bool:
    from src.curriculum.library.objects.object_search import _matches_all_train_pairs

    return _matches_all_train_pairs(build_derived_steps(composition), task)


def _map_param(param, mapping: Dict[int, int]):
    if param is not None and param.kind == "literal":
        return ParamSource("literal", mapping.get(param.value, param.value))
    return param


def _mapped(composition: DerivedComposition, mapping: Dict[int, int]) -> DerivedComposition:
    actions = tuple(Action(a.name, _map_param(a.param, mapping), a.selection, a.target, a.extra) for a in composition.actions)
    return DerivedComposition(composition.region, actions)


def _colour_testable(composition: DerivedComposition) -> bool:
    return not any(a.param is not None and a.param.kind in _TABLE_KINDS for a in composition.actions)


def _pair_key(pair) -> tuple:
    return (tuple(map(tuple, pair.input)), tuple(map(tuple, pair.output)))


def demos_invariant(task: Task, fn: Callable[[Grid], Grid]) -> bool:
    """True when the transform maps the set of demonstration pairs onto itself."""
    seen = {_pair_key(pair) for pair in task.train}
    return all(_pair_key(pair) in seen for pair in transformed_task(task, fn).train)


def _colour_check(task: Task, composition: DerivedComposition) -> bool:
    mapping = color_permutation(task, composition.region.background)
    if not mapping or not demos_invariant(task, lambda g: [[mapping.get(v, v) for v in row] for row in g]):
        return True
    return _matches(_mapped(composition, mapping), permuted_task(task, mapping))


def _oriented(composition: DerivedComposition, name: str) -> DerivedComposition:
    """The same rule after the transform: axis swaps exchange row and column segments."""
    kind = composition.region.kind
    if name not in _AXIS_SWAPS or kind not in _KIND_SWAP:
        return composition
    return DerivedComposition(composition.region._replace(kind=_KIND_SWAP[kind]), composition.actions)


def _geometric_failures(task: Task, composition: DerivedComposition) -> List[str]:
    return [
        name
        for name, fn in GEOMETRIC.items()
        if demos_invariant(task, fn) and not _matches(_oriented(composition, name), transformed_task(task, fn))
    ]


def check_equivariance(task: Task, composition: DerivedComposition) -> Equivariance:
    failed = _geometric_failures(task, composition)
    if _colour_testable(composition) and not _colour_check(task, composition):
        failed.append("colors")
    return Equivariance(not failed, failed)
