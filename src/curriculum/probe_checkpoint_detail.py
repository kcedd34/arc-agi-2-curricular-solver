"""Probe-pool checkpoint with per-task solved/exact-match detail (RN-CUR-05).

`probe.py::run_probe_checkpoint` only returns aggregate counts. Section
5.6 of object-pack.md needs the actual newly-solved task IDs too, so
they can be desk-check validated (same rigor as the curricular gate,
object_pack_gate.py). This module reuses `search_task` and the same
scoring helpers `run_probe_checkpoint` uses (RN-CUR-31: no duplicate
counting logic, only the extra bookkeeping of which IDs solved).

RN-CUR-32/ADR 0063: full per-task detail goes to a file, terminal stays
short.
"""
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from src.curriculum.cli_output import print_summary, write_detail
from src.curriculum.evaluator.exact_match import score_task
from src.curriculum.evaluator.solutions import load_task_solutions
from src.curriculum.loader import load_task
from src.curriculum.probe import DEFAULT_TRAINING_DIR, load_probe_pool
from src.curriculum.search.rank import search_task

DEFAULT_REPORT_PATH = Path("outputs/curriculum/probe-checkpoint-v5-detail.txt")


@dataclass
class ProbeCheckpointDetail:
    num_tasks: int
    solved_task_ids: List[str]
    exact_match_task_ids: List[str]
    elapsed_s: float


def run_probe_checkpoint_detail(
    probe_pool: List[str], training_dir: Path = DEFAULT_TRAINING_DIR
) -> ProbeCheckpointDetail:
    solved_task_ids: List[str] = []
    exact_match_task_ids: List[str] = []

    start = time.time()
    for task_id in probe_pool:
        task_path = training_dir / f"{task_id}.json"
        task = load_task(task_path)
        result = search_task(task)
        if result.status != "solved":
            continue
        solved_task_ids.append(task_id)
        solutions = load_task_solutions(task_path)
        score = score_task(result.predictions, solutions)
        if score["all_exact_match"]:
            exact_match_task_ids.append(task_id)

    return ProbeCheckpointDetail(
        num_tasks=len(probe_pool),
        solved_task_ids=solved_task_ids,
        exact_match_task_ids=exact_match_task_ids,
        elapsed_s=time.time() - start,
    )


def format_report(detail: ProbeCheckpointDetail) -> str:
    lines = [
        f"Probe pool checkpoint (v5, object pack promoted): {detail.num_tasks} tasks",
        f"Solved: {len(detail.solved_task_ids)}",
        f"Exact match: {len(detail.exact_match_task_ids)}",
        f"Elapsed: {detail.elapsed_s:.1f}s ({detail.elapsed_s / detail.num_tasks:.2f}s/task)",
        "",
        "Solved task IDs:",
        *[f"  - {t}" for t in detail.solved_task_ids],
        "",
        "Exact-match task IDs:",
        *[f"  - {t}" for t in detail.exact_match_task_ids],
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    probe_pool = load_probe_pool()
    detail = run_probe_checkpoint_detail(probe_pool)

    detail_path = write_detail(format_report(detail), DEFAULT_REPORT_PATH)
    print_summary(
        [
            f"Probe pool: {detail.num_tasks} tasks",
            f"Solved: {len(detail.solved_task_ids)}",
            f"Exact match: {len(detail.exact_match_task_ids)}",
            f"Elapsed: {detail.elapsed_s:.1f}s ({detail.elapsed_s / detail.num_tasks:.2f}s/task)",
        ],
        detail_path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
