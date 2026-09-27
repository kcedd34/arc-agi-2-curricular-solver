"""Phase 7 curricular gate for the object pack (RN-CUR-36 condition 2,
object-pack.md Section 5.5): runs `check_with_object_pack` across every
curricular-pool task not already in `solved_tasks`, deciding whether the
object pack earns promotion out of staging (>=2 desk-check-validated
hits, per RN-CUR-36). Run for real on 2026-09-22 (797 tasks: 16 solved,
7 object-pack-only hits desk-check-validated as coherent after
excluding one false positive; condition met, package promoted to
`library/objects/`, see `search/rank.py::search_task`). This module is
kept as the reusable gate driver for any future package's promotion
check, not just a one-shot script.

RN-CUR-32/ADR 0063: the CLI entry point below writes full per-task
detail to a file and prints only a short summary to the terminal.

2026-09-22 correction: `resolved_task_ids` used to accept on
`combined.status == "solved"`, which only means every verified
candidate agreed with every other one (`unanimous`), never that the
shared prediction matched the real gabarito. Acceptance now goes
through `verified_verdict.compute_verified_verdict`, whose `solved`
field is the real, two-attempt, gabarito-checked verdict (RN-CUR-04).
`unanimous` is kept as a separate, non-acceptance field so the false-
positive class (unanimous but wrong) stays visible in the report.
"""
import argparse
import functools
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from src.curriculum.cli_output import print_summary, write_detail
from src.curriculum.parallel_batch import add_worker_arguments, resolve_workers, run_batch
from src.curriculum.select import DEFAULT_PARTITION_PATH, load_curricular_pool
from src.curriculum.state import DEFAULT_STATE_PATH, CurriculumState, load_state
from src.curriculum.solved_split import count_split, format_split, ids_solved_at_2
from src.curriculum.timing import RunTiming, TimedResult, summarize_timing, with_timing
from src.curriculum.timing_report import timing_line, write_task_times
from src.curriculum.verified_verdict import compute_verified_verdict

DEFAULT_TRAINING_DIR = Path("data/ARC-AGI-2/data/training")
DEFAULT_REPORT_PATH = Path("outputs/curriculum/object-pack-gate-report.txt")
GATE_TIMES_PATH = Path("outputs/curriculum/gate-task-times.json")


@dataclass
class GateTaskResult:
    task_id: str
    unanimous: bool
    solved: bool
    object_verified_count: int
    main_verified_count: int
    error: Optional[str] = None
    solved_at_1: bool = False
    budget_hit: bool = False
    deadline_hit: bool = False


def not_yet_accepted_pool(state: CurriculumState, curricular_pool: List[str]) -> List[str]:
    solved = set(state.solved_tasks)
    return [task_id for task_id in curricular_pool if task_id not in solved]


def _gate_worker(task_id: str, training_dir: Path) -> GateTaskResult:
    verdict = compute_verified_verdict(task_id, training_dir)
    return GateTaskResult(
        task_id=verdict.task_id,
        unanimous=verdict.unanimous,
        solved=verdict.solved,
        object_verified_count=verdict.object_verified_count,
        main_verified_count=verdict.main_verified_count,
        error=verdict.error,
        solved_at_1=verdict.solved_at_1,
        budget_hit=verdict.budget_hit,
        deadline_hit=verdict.deadline_hit,
    )


def run_gate_check_timed(
    task_ids: List[str],
    training_dir: Path = DEFAULT_TRAINING_DIR,
    max_workers: Optional[int] = None,
) -> Tuple[List[GateTaskResult], RunTiming]:
    """Gate results plus per-task timing (RN-CUR-38)."""
    worker = with_timing(functools.partial(_gate_worker, training_dir=training_dir))
    wall_start = time.perf_counter()
    outcomes = run_batch(task_ids, worker, max_workers=max_workers)
    wall_seconds = time.perf_counter() - wall_start
    results = [
        outcome.value if isinstance(outcome, TimedResult)
        else GateTaskResult(task_id=task_id, unanimous=False, solved=False, object_verified_count=0,
                             main_verified_count=0, error=repr(outcome))
        for task_id, outcome in outcomes
    ]
    return results, summarize_timing(outcomes, wall_seconds)


def run_gate_check(
    task_ids: List[str],
    training_dir: Path = DEFAULT_TRAINING_DIR,
    max_workers: Optional[int] = None,
) -> List[GateTaskResult]:
    return run_gate_check_timed(task_ids, training_dir, max_workers)[0]


def resolved_task_ids(results: List[GateTaskResult]) -> List[str]:
    return [r.task_id for r in results if r.solved]


def false_positive_task_ids(results: List[GateTaskResult]) -> List[str]:
    """Unanimous among verified candidates but wrong against the gabarito;
    the exact class that caused the 2026-09-22 wrongful acceptances."""
    return [r.task_id for r in results if r.unanimous and not r.solved]


def budget_cut_counts(results: List[GateTaskResult]) -> Tuple[int, int]:
    """(tasks that hit the sequence work budget, tasks that hit the safety deadline), ADR 0101."""
    return sum(r.budget_hit for r in results), sum(r.deadline_hit for r in results)


def budget_line(results: List[GateTaskResult]) -> str:
    budget, deadline = budget_cut_counts(results)
    return f"Sequence budget cuts: budget_hit={budget} deadline_hit={deadline} of {len(results)}"


def format_gate_report(results: List[GateTaskResult]) -> str:
    resolved = resolved_task_ids(results)
    false_positives = false_positive_task_ids(results)
    lines = [
        f"Curricular gate check: {len(results)} tasks not yet accepted",
        f"Solved (gabarito-verified, two-attempt): {format_split(count_split(results))}",
        f"Unanimous-but-wrong (would have been false accepts under the old rule): {len(false_positives)}",
    ]
    lines.append(f"Solved only by attempt 2: {ids_solved_at_2(results)}")
    lines.append(budget_line(results))
    lines.append(f"budget_hit tasks: {[r.task_id for r in results if r.budget_hit]}")
    lines.append(f"deadline_hit tasks: {[r.task_id for r in results if r.deadline_hit]}")
    lines.extend(f"  - {task_id}" for task_id in resolved)
    lines.append("")
    lines.append("Per-task detail (task_id: unanimous=X solved=Y object_verified=N main_verified=N):")
    for r in results:
        lines.append(
            f"{r.task_id}: unanimous={r.unanimous} solved={r.solved} at1={r.solved_at_1} object_verified={r.object_verified_count} "
            f"main_verified={r.main_verified_count} budget_hit={r.budget_hit} deadline_hit={r.deadline_hit}"
        )
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    add_worker_arguments(parser)
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    workers_used = resolve_workers(args.workers, args.sequential)

    state = load_state(DEFAULT_STATE_PATH)
    pool = load_curricular_pool(DEFAULT_PARTITION_PATH)
    task_ids = not_yet_accepted_pool(state, pool)

    results, timing = run_gate_check_timed(task_ids, max_workers=workers_used)
    write_task_times(GATE_TIMES_PATH, timing)
    resolved = resolved_task_ids(results)

    detail_path = write_detail(format_gate_report(results), DEFAULT_REPORT_PATH)
    print_summary(
        [
            f"Tasks checked: {len(results)} (workers={workers_used})",
            timing_line(timing, workers_used),
            budget_line(results),
            f"Resolved: {format_split(count_split(results))}",
            *[f"  - {task_id}" for task_id in resolved],
        ],
        detail_path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
