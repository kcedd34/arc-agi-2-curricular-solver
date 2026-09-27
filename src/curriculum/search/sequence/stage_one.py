"""First-rule admission for two-rule sequences (ADR 0097, decision 3).

A first rule is admissible when it is monotone (every cell it changes takes
the target output value), changes at least one cell, and does not solve the
task alone. Admission is decided from the train pairs only."""
from typing import Any, Dict, Iterator, List, NamedTuple, Optional, Tuple

from src.curriculum.grid import Grid
from src.curriculum.library.objects.object_search import enumerate_object_compositions
from src.curriculum.loader import Task
from src.curriculum.search.compose import enumerate_compositions
from src.curriculum.spec import work_meter
from src.curriculum.search.sequence.composition import build_stage_steps, run_steps

MAX_FIRST_STAGE = 10


class FirstStage(NamedTuple):
    candidate: Any
    train_grids: List[Grid]
    test_grids: List[Grid]
    fixed_cells: int
    num_steps: int


def is_same_shape_task(task: Task) -> bool:
    return all(
        len(p.input) == len(p.output) and len(p.input[0]) == len(p.output[0]) for p in task.train
    )


def monotone_fixed_cells(source: Grid, inter: Grid, target: Grid) -> Optional[int]:
    """Number of cells the rule changed, or None if any changed cell does
    not take the target value (or the shape differs)."""
    if len(inter) != len(source) or len(inter[0]) != len(source[0]):
        return None
    fixed = 0
    for r, row in enumerate(source):
        for c, value in enumerate(row):
            if inter[r][c] == value:
                continue
            if inter[r][c] != target[r][c]:
                return None
            fixed += 1
    return fixed


def _train_intermediates(steps, task: Task) -> Optional[Tuple[List[Grid], int]]:
    grids: List[Grid] = []
    total = 0
    for pair in task.train:
        inter = run_steps(steps, pair.input)
        if inter is None:
            return None
        fixed = monotone_fixed_cells(pair.input, inter, pair.output)
        if fixed is None:
            return None
        grids.append(inter)
        total += fixed
    return grids, total


def _admit(candidate: Any, task: Task) -> Optional[FirstStage]:
    steps = build_stage_steps(candidate)
    result = _train_intermediates(steps, task)
    if result is None:
        return None
    grids, fixed = result
    if fixed == 0 or all(g == p.output for g, p in zip(grids, task.train)):
        return None
    tests = [run_steps(steps, g) for g in task.test_inputs]
    if any(t is None for t in tests):
        return None
    return FirstStage(candidate, grids, tests, fixed, len(steps))


def _all_candidates(task: Task) -> Iterator[Any]:
    yield from enumerate_compositions(task)
    yield from enumerate_object_compositions(task)


def _grids_key(grids: List[Grid]) -> tuple:
    return tuple(tuple(map(tuple, g)) for g in grids)


def _scan_first_stages(task: Task) -> Dict[tuple, FirstStage]:
    best: Dict[tuple, FirstStage] = {}
    try:
        for candidate in _all_candidates(task):
            stage = _admit(candidate, task)
            if stage is None:
                continue
            key = _grids_key(stage.train_grids)
            if key not in best or stage.num_steps < best[key].num_steps:
                best[key] = stage
    except work_meter.WorkBudgetExceeded:
        pass
    return best


def admissible_first_stages(task: Task, limit: int = MAX_FIRST_STAGE) -> List[FirstStage]:
    if not is_same_shape_task(task):
        return []
    best = _scan_first_stages(task)
    ranked = sorted(best.values(), key=lambda s: (-s.fixed_cells, s.num_steps, s.candidate.describe()))
    return ranked[:limit]
