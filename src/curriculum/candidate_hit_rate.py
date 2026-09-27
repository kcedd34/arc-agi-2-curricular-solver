"""Candidate-choice hit-rate analysis (item 2 of the 2026-09-22 follow-up
request): among curricular-gate tasks with at least one verified
candidate, how often does the simplest verified candidate's prediction
match the gabarito (top-1), and how often is the gabarito matched by
one of the two simplest distinct predictions (top-2).

Post-hoc only (RN-CUR-03): `search/candidate_rank.py` ranks candidates
by simplicity with no gabarito access at all; only this module reads
test outputs, via `evaluator/solutions.py`, exactly like `probe.py` and
`object_pack_gate.py`'s own desk-check measurements already do.
"""
import functools
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from src.curriculum.cli_output import print_summary, write_detail
from src.curriculum.evaluator.exact_match import score_task
from src.curriculum.evaluator.solutions import load_task_solutions
from src.curriculum.loader import load_task
from src.curriculum.object_pack_gate import DEFAULT_PARTITION_PATH, DEFAULT_STATE_PATH, not_yet_accepted_pool
from src.curriculum.parallel_batch import run_batch
from src.curriculum.select import load_curricular_pool
from src.curriculum.state import load_state

DEFAULT_TRAINING_DIR = Path("data/ARC-AGI-2/data/training")
DEFAULT_REPORT_PATH = Path("outputs/curriculum/candidate-hit-rate-detail.txt")


@dataclass
class HitRateTaskResult:
    task_id: str
    num_verified_candidates: int
    top1_match: Optional[bool]
    top2_match: Optional[bool]
    error: Optional[str] = None


def _matches_gabarito(predictions, solutions) -> bool:
    return bool(score_task(predictions, solutions)["all_exact_match"])


def _hit_rate_worker(task_id: str, training_dir: Path) -> HitRateTaskResult:
    from src.curriculum.search.candidate_rank import verified_candidates_ranked_by_simplicity

    try:
        task_path = training_dir / f"{task_id}.json"
        task = load_task(task_path)
        ranked = verified_candidates_ranked_by_simplicity(task)
        if not ranked:
            return HitRateTaskResult(task_id, num_verified_candidates=0, top1_match=None, top2_match=None)

        solutions = load_task_solutions(task_path)
        top1 = _matches_gabarito(ranked[0][1], solutions)
        top2 = top1 or (len(ranked) > 1 and _matches_gabarito(ranked[1][1], solutions))
        return HitRateTaskResult(task_id, num_verified_candidates=len(ranked), top1_match=top1, top2_match=top2)
    except Exception as exc:  # isolated per-task failure, RN-CUR-32 batch discipline
        return HitRateTaskResult(task_id, num_verified_candidates=0, top1_match=None, top2_match=None, error=repr(exc))


def run_hit_rate_analysis(
    task_ids: List[str], training_dir: Path = DEFAULT_TRAINING_DIR, max_workers: Optional[int] = None
) -> List[HitRateTaskResult]:
    worker = functools.partial(_hit_rate_worker, training_dir=training_dir)
    outcomes = run_batch(task_ids, worker, max_workers=max_workers)
    return [
        result if not isinstance(result, BaseException)
        else HitRateTaskResult(task_id, num_verified_candidates=0, top1_match=None, top2_match=None, error=repr(result))
        for task_id, result in outcomes
    ]


def summarize(results: List[HitRateTaskResult]) -> Dict[str, object]:
    with_candidates = [r for r in results if r.error is None and r.num_verified_candidates > 0]
    n = len(with_candidates)
    top1_rate = sum(1 for r in with_candidates if r.top1_match) / n if n else 0.0
    top2_rate = sum(1 for r in with_candidates if r.top2_match) / n if n else 0.0
    distribution: Dict[int, int] = {}
    for r in with_candidates:
        distribution[r.num_verified_candidates] = distribution.get(r.num_verified_candidates, 0) + 1
    errors = [r.task_id for r in results if r.error is not None]
    return {
        "n_tasks_with_candidates": n,
        "top1_rate": top1_rate,
        "top2_rate": top2_rate,
        "distribution": distribution,
        "errors": errors,
    }


def format_report(results: List[HitRateTaskResult], summary: Dict[str, object]) -> str:
    lines = [
        f"Candidate-choice hit-rate analysis: {len(results)} gate tasks",
        f"Tasks with >=1 verified candidate: {summary['n_tasks_with_candidates']}",
        f"Top-1 hit rate: {summary['top1_rate']:.4f}",
        f"Top-2 hit rate: {summary['top2_rate']:.4f}",
        "Distribution of verified-candidate count (count -> num tasks):",
    ]
    for count in sorted(summary["distribution"]):
        lines.append(f"  {count} -> {summary['distribution'][count]}")
    if summary["errors"]:
        lines.append(f"Errors ({len(summary['errors'])}): {summary['errors']}")
    lines.append("")
    lines.append("Per-task detail (task_id: num_verified top1=X top2=Y):")
    for r in results:
        lines.append(f"{r.task_id}: num_verified={r.num_verified_candidates} top1={r.top1_match} top2={r.top2_match}")
    return "\n".join(lines)


def main(argv=None) -> int:
    state = load_state(DEFAULT_STATE_PATH)
    pool = load_curricular_pool(DEFAULT_PARTITION_PATH)
    task_ids = not_yet_accepted_pool(state, pool)

    results = run_hit_rate_analysis(task_ids)
    summary = summarize(results)

    detail_path = write_detail(format_report(results, summary), DEFAULT_REPORT_PATH)
    print_summary(
        [
            f"Tasks checked: {len(results)}",
            f"With >=1 verified candidate: {summary['n_tasks_with_candidates']}",
            f"Top-1 hit rate: {summary['top1_rate']:.4f}",
            f"Top-2 hit rate: {summary['top2_rate']:.4f}",
        ],
        detail_path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
