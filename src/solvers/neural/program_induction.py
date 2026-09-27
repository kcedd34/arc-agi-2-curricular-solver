"""Pure induce-verify-apply orchestration (ADR 0060), given a list of
already-generated raw completions. No GPU dependency here; sampling the
completions themselves lives in program_generation.py.
"""
from typing import List, NamedTuple, Optional

from src.solvers.neural.program_extraction import build_program_source, extract_program_body
from src.solvers.neural.program_verification import (
    run_program_on_grid,
    verify_program_against_train_pairs,
)
from src.utils.grid_types import Grid
from src.utils.task_loader import Task


class InductionResult(NamedTuple):
    verified_programs: List[str]
    is_ambiguous: bool
    chosen_program: Optional[str]


def _candidates_from_completions(completions: List[str]) -> List[str]:
    candidates = []
    for completion in completions:
        body = extract_program_body(completion)
        if body is not None:
            candidates.append(build_program_source(body))
    return candidates


def _verified_survivors(programs: List[str], task: Task) -> List[str]:
    seen = set()
    survivors = []
    for program in programs:
        if program in seen:
            continue
        seen.add(program)
        if verify_program_against_train_pairs(program, task.train):
            survivors.append(program)
    return sorted(survivors, key=len)


def _freeze(grid: Optional[Grid]):
    return tuple(tuple(row) for row in grid) if grid is not None else None


def _agree_on_every_test_input(survivors: List[str], task: Task) -> bool:
    for pair in task.test:
        outputs = {_freeze(run_program_on_grid(program, pair.input)) for program in survivors}
        if len(outputs) > 1:
            return False
    return True


def induce_verified_program(completions: List[str], task: Task) -> InductionResult:
    candidates = _candidates_from_completions(completions)
    survivors = _verified_survivors(candidates, task)
    if not survivors:
        return InductionResult(verified_programs=[], is_ambiguous=False, chosen_program=None)
    if len(survivors) == 1 or _agree_on_every_test_input(survivors, task):
        return InductionResult(verified_programs=survivors, is_ambiguous=False, chosen_program=survivors[0])
    return InductionResult(verified_programs=survivors, is_ambiguous=True, chosen_program=None)


def apply_program_to_test(program: str, task: Task) -> List[Optional[Grid]]:
    return [run_program_on_grid(program, pair.input) for pair in task.test]
