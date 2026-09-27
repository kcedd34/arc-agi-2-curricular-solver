"""Two-attempt policy for gate tasks with more than one disagreeing
verified candidate (item 3 of the 2026-09-22 follow-up request,
RN-CUR-04's "regra de duas tentativas"): submit the two simplest
distinct verified predictions as attempt_1 and attempt_2, and report a
task resolved only if at least one of the two matches the gabarito.

RN-CUR-03: candidate selection itself
(`search/candidate_rank.py::verified_candidates_ranked_by_simplicity`)
never touches gabaritos; only the pass/fail verdict below does, via
`evaluator/solutions.py`, exactly like `probe.py` already does. This
module measures which currently-`ambiguous` gate tasks would resolve
under the policy; it does not itself mutate `solved_tasks` in
state.json, since accepting new tasks under a new policy is a separate
decision (mirrors RN-CUR-36's own promotion gate for the object pack).

The actual two-attempt-vs-gabarito logic lives in `verified_verdict.py`
(the pipeline-wide `solved` definition after the 2026-09-22 unanimous-
vs-solved correction); this module is now a thin wrapper reporting that
verdict under `TwoAttemptResult`'s pre-existing shape.
"""
import functools
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from src.curriculum.cli_output import print_summary, write_detail
from src.curriculum.parallel_batch import run_batch
from src.curriculum.verified_verdict import compute_verified_verdict, distinct_attempts as _distinct_attempts

DEFAULT_TRAINING_DIR = Path("data/ARC-AGI-2/data/training")
DEFAULT_REPORT_PATH = Path("outputs/curriculum/two-attempt-detail.txt")


@dataclass
class TwoAttemptResult:
    task_id: str
    num_verified_candidates: int
    attempt_1_match: Optional[bool]
    attempt_2_match: Optional[bool]
    resolved: bool
    error: Optional[str] = None


def _two_attempt_worker(task_id: str, training_dir: Path) -> TwoAttemptResult:
    verdict = compute_verified_verdict(task_id, training_dir)
    return TwoAttemptResult(
        verdict.task_id,
        verdict.num_verified_candidates,
        verdict.attempt_1_match,
        verdict.attempt_2_match,
        resolved=verdict.solved,
        error=verdict.error,
    )


def run_two_attempt_check(
    task_ids: List[str], training_dir: Path = DEFAULT_TRAINING_DIR, max_workers: Optional[int] = None
) -> List[TwoAttemptResult]:
    worker = functools.partial(_two_attempt_worker, training_dir=training_dir)
    outcomes = run_batch(task_ids, worker, max_workers=max_workers)
    return [
        result if not isinstance(result, BaseException)
        else TwoAttemptResult(task_id, 0, None, None, resolved=False, error=repr(result))
        for task_id, result in outcomes
    ]


def format_report(results: List[TwoAttemptResult]) -> str:
    resolved = [r for r in results if r.resolved]
    lines = [
        f"Two-attempt policy check: {len(results)} previously-ambiguous tasks",
        f"Now resolved (attempt_1 or attempt_2 matches gabarito): {len(resolved)}",
    ]
    lines.extend(f"  - {r.task_id}" for r in resolved)
    lines.append("")
    lines.append("Per-task detail (task_id: num_verified attempt_1=X attempt_2=Y resolved=Z):")
    for r in results:
        lines.append(
            f"{r.task_id}: num_verified={r.num_verified_candidates} "
            f"attempt_1={r.attempt_1_match} attempt_2={r.attempt_2_match} resolved={r.resolved}"
        )
    return "\n".join(lines)


def main(argv, task_ids: List[str]) -> int:
    results = run_two_attempt_check(task_ids)
    detail_path = write_detail(format_report(results), DEFAULT_REPORT_PATH)
    resolved = [r for r in results if r.resolved]
    print_summary(
        [
            f"Previously-ambiguous tasks checked: {len(results)}",
            f"Now resolved: {len(resolved)}",
            *[f"  - {r.task_id}" for r in resolved],
        ],
        detail_path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(1)  # this driver needs the ambiguous task_ids from a gate run; see cli usage in progress.md
