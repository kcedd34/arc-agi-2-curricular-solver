"""Probe-pool checkpoint: an honest generalization score, RN-CUR-05.

Only this module (plus evaluator/solutions.py, which it delegates to
for gabaritos) reads probe-pool test outputs; curricular selection and
search never do. The probe pool exists to catch overfitting to the
curricular pool, not to be trained or searched against.

2026-09-22 correction: `solved` here used to mean "every verified
candidate agreed" (unanimous) and, worse, non-unanimous tasks were
never even checked against the gabarito (no two-attempt fallback). Both
are fixed by delegating to `verified_verdict.compute_verified_verdict`,
which applies RN-CUR-04's two-attempt policy to every task and reports
`unanimous`/`solved` as separate fields; `accuracy` is unchanged in
meaning (it was already a real gabarito-based rate) but is now computed
from the corrected, universally-applied `solved` field.
"""
import functools
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from src.curriculum.parallel_batch import run_batch
from src.curriculum.timing import RunTiming, TimedResult, summarize_timing, with_timing
from src.curriculum.solved_split import count_split
from src.curriculum.verified_verdict import compute_verified_verdict

DEFAULT_TRAINING_DIR = Path("data/ARC-AGI-2/data/training")
DEFAULT_PARTITION_PATH = Path("docs/curriculum/partition.json")


def load_probe_pool(path: Path = DEFAULT_PARTITION_PATH) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return raw["probe_pool"]


@dataclass
class ProbeCheckpoint:
    date: str
    num_tasks: int
    num_unanimous: int
    num_solved: int
    accuracy: float
    num_solved_at_1: int = 0
    num_solved_at_2: int = 0
    num_budget_hit: int = 0
    num_deadline_hit: int = 0


@dataclass
class ProbeTaskResult:
    task_id: str
    unanimous: bool
    solved: bool
    error: Optional[str] = None
    solved_at_1: bool = False
    budget_hit: bool = False
    deadline_hit: bool = False


def _probe_worker(task_id: str, training_dir: Path) -> ProbeTaskResult:
    verdict = compute_verified_verdict(task_id, training_dir)
    return ProbeTaskResult(task_id=verdict.task_id, unanimous=verdict.unanimous, solved=verdict.solved,
                            error=verdict.error, solved_at_1=verdict.solved_at_1,
                            budget_hit=verdict.budget_hit, deadline_hit=verdict.deadline_hit)


def _task_results_from_outcomes(outcomes) -> List[ProbeTaskResult]:
    return [
        result if not isinstance(result, BaseException)
        else ProbeTaskResult(task_id=task_id, unanimous=False, solved=False, error=repr(result))
        for task_id, result in outcomes
    ]


def _checkpoint_from_task_results(
    probe_pool: List[str], date: str, task_results: List[ProbeTaskResult]
) -> ProbeCheckpoint:
    num_unanimous = sum(1 for r in task_results if r.unanimous)
    split = count_split(task_results)
    num_solved = split.total
    num_tasks = len(probe_pool)
    accuracy = num_solved / num_tasks if num_tasks else 0.0
    return ProbeCheckpoint(
        date=date,
        num_tasks=num_tasks,
        num_unanimous=num_unanimous,
        num_solved=num_solved,
        accuracy=accuracy,
        num_solved_at_1=split.at1,
        num_solved_at_2=split.at2,
        num_budget_hit=sum(r.budget_hit for r in task_results),
        num_deadline_hit=sum(r.deadline_hit for r in task_results),
    )


def run_probe_checkpoint(
    probe_pool: List[str],
    date: str,
    training_dir: Path = DEFAULT_TRAINING_DIR,
    max_workers: Optional[int] = None,
) -> ProbeCheckpoint:
    worker = functools.partial(_probe_worker, training_dir=training_dir)
    outcomes = run_batch(probe_pool, worker, max_workers=max_workers)
    task_results = _task_results_from_outcomes(outcomes)
    return _checkpoint_from_task_results(probe_pool, date, task_results)


def run_probe_detail_timed(
    probe_pool: List[str],
    training_dir: Path = DEFAULT_TRAINING_DIR,
    max_workers: Optional[int] = None,
) -> Tuple[List[ProbeTaskResult], RunTiming]:
    """Per-task results plus timing (continuous-loop.md Fase E.4)."""
    worker = with_timing(functools.partial(_probe_worker, training_dir=training_dir))
    wall_start = time.perf_counter()
    outcomes = run_batch(probe_pool, worker, max_workers=max_workers)
    wall_seconds = time.perf_counter() - wall_start
    unwrapped = [
        (task_id, outcome.value if isinstance(outcome, TimedResult) else outcome)
        for task_id, outcome in outcomes
    ]
    return _task_results_from_outcomes(unwrapped), summarize_timing(outcomes, wall_seconds)


def run_probe_checkpoint_timed(
    probe_pool: List[str],
    date: str,
    training_dir: Path = DEFAULT_TRAINING_DIR,
    max_workers: Optional[int] = None,
) -> Tuple[ProbeCheckpoint, RunTiming]:
    """Same contract as `run_probe_checkpoint`, plus wall/mean/max task
    timing. Kept separate so the untimed function's return type, and
    `state.json`'s stored checkpoint shape, stay unchanged."""
    task_results, timing = run_probe_detail_timed(probe_pool, training_dir, max_workers)
    return _checkpoint_from_task_results(probe_pool, date, task_results), timing
