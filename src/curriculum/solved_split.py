"""solved@1 / solved@2 split of a batch of verdicts (ADR 0083).

`solved@1`: attempt 1 matched the gabarito. `solved@2`: solved, but only
attempt 2 matched. `total = at1 + at2` is the same `solved` count every
measurement already reported. A drop in `at2` at constant `total` means
the simplicity ranking is putting the right answer first more often.

Works on any result object exposing boolean `solved` and `solved_at_1`
(probe, gate and scale-test task results).
"""
from dataclasses import dataclass
from typing import Any, Iterable, List


@dataclass(frozen=True)
class SolvedSplit:
    total: int
    at1: int
    at2: int


def count_split(results: Iterable[Any]) -> SolvedSplit:
    results = list(results)
    total = sum(1 for r in results if r.solved)
    at1 = sum(1 for r in results if r.solved and r.solved_at_1)
    return SolvedSplit(total=total, at1=at1, at2=total - at1)


def ids_solved_at_2(results: Iterable[Any]) -> List[str]:
    return [r.task_id for r in results if r.solved and not r.solved_at_1]


def format_split(split: SolvedSplit) -> str:
    return f"solved={split.total} (@1={split.at1}, @2={split.at2})"
