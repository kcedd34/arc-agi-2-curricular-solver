"""Per-task diagnostic probe for continuous-loop.md Fase A.3/A.4: real
candidate counts, solved verdict, and whether either composition search
hit its 5000-item cap (RN-CUR-30: real execution, not inference from
stated pool-level counts).
"""
import functools
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from src.curriculum.library.objects.object_search import (
    MAX_OBJECT_COMPOSITIONS_PER_TASK,
    enumerate_object_compositions,
)
from src.curriculum.loader import load_task
from src.curriculum.parallel_batch import run_batch
from src.curriculum.search.compose import MAX_COMPOSITIONS_PER_TASK, enumerate_compositions
from src.curriculum.timing import RunTiming, TimedResult, summarize_timing, with_timing
from src.curriculum.verified_verdict import compute_verified_verdict

DEFAULT_TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


@dataclass
class CandidateProbeResult:
    task_id: str
    num_verified_candidates: int
    main_verified_count: int
    object_verified_count: int
    solved: bool
    unanimous: bool
    main_cap_hit: bool
    object_cap_hit: bool
    error: Optional[str] = None


def _cap_hit_counts(task, training_dir: Path) -> (bool, bool):
    task_obj = task if not isinstance(task, (str, Path)) else load_task(training_dir / f"{task}.json")
    main_raw = sum(1 for _ in enumerate_compositions(task_obj))
    object_raw = sum(1 for _ in enumerate_object_compositions(task_obj))
    return main_raw >= MAX_COMPOSITIONS_PER_TASK, object_raw >= MAX_OBJECT_COMPOSITIONS_PER_TASK


def _probe_worker(task_id: str, training_dir: Path) -> CandidateProbeResult:
    verdict = compute_verified_verdict(task_id, training_dir)
    if verdict.error is not None:
        return CandidateProbeResult(
            task_id=task_id, num_verified_candidates=0, main_verified_count=0, object_verified_count=0,
            solved=False, unanimous=False, main_cap_hit=False, object_cap_hit=False, error=verdict.error,
        )
    task_path = training_dir / f"{task_id}.json"
    task = load_task(task_path)
    main_cap_hit, object_cap_hit = _cap_hit_counts(task, training_dir)
    return CandidateProbeResult(
        task_id=task_id,
        num_verified_candidates=verdict.num_verified_candidates,
        main_verified_count=verdict.main_verified_count,
        object_verified_count=verdict.object_verified_count,
        solved=verdict.solved,
        unanimous=verdict.unanimous,
        main_cap_hit=main_cap_hit,
        object_cap_hit=object_cap_hit,
    )


def _fallback_result(task_id: str, error: BaseException) -> CandidateProbeResult:
    return CandidateProbeResult(
        task_id=task_id, num_verified_candidates=0, main_verified_count=0, object_verified_count=0,
        solved=False, unanimous=False, main_cap_hit=False, object_cap_hit=False, error=repr(error),
    )


def run_candidate_probe(
    task_ids: List[str],
    training_dir: Path = DEFAULT_TRAINING_DIR,
    max_workers: Optional[int] = None,
) -> List[CandidateProbeResult]:
    worker = functools.partial(_probe_worker, training_dir=training_dir)
    outcomes = run_batch(task_ids, worker, max_workers=max_workers)
    return [
        result if not isinstance(result, BaseException) else _fallback_result(task_id, result)
        for task_id, result in outcomes
    ]


def run_candidate_probe_timed(
    task_ids: List[str],
    training_dir: Path = DEFAULT_TRAINING_DIR,
    max_workers: Optional[int] = None,
) -> Tuple[List[CandidateProbeResult], RunTiming]:
    """Same contract as `run_candidate_probe`, plus wall/mean/max task
    timing (continuous-loop.md Fase A.4/E.4), used by round_report.py so
    Fases A and E are instrumented without changing the untimed
    function's existing return type or its own tests."""
    worker = with_timing(functools.partial(_probe_worker, training_dir=training_dir))
    wall_start = time.perf_counter()
    outcomes = run_batch(task_ids, worker, max_workers=max_workers)
    wall_seconds = time.perf_counter() - wall_start
    results = [
        outcome.value if isinstance(outcome, TimedResult) else _fallback_result(task_id, outcome)
        for task_id, outcome in outcomes
    ]
    return results, summarize_timing(outcomes, wall_seconds)
