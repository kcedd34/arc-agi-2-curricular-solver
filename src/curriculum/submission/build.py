"""CLI: official challenges file -> validated submission.json (ADR 0104)."""
import argparse
import json
import os
from pathlib import Path
from typing import Dict

from src.curriculum.cli_output import print_summary, write_detail
from src.curriculum.loader import Task
from src.curriculum.parallel_batch import default_worker_count
from src.curriculum.submission.challenges import load_challenges
from src.curriculum.submission.format import build_entries, validate_submission
from src.curriculum.submission.predict import solve_task_attempts
from src.curriculum.submission.runner import TaskOutcome, run_tasks

PER_TASK_SECONDS = 1200.0
GLOBAL_SECONDS = 7 * 3600.0


def assemble(tasks: Dict[str, Task], outcomes: Dict[str, TaskOutcome]) -> dict:
    return {tid: build_entries(task, outcomes[tid].attempts) for tid, task in tasks.items()}


def _report(outcomes: Dict[str, TaskOutcome], wall: float) -> dict:
    counts: Dict[str, int] = {}
    for outcome in outcomes.values():
        counts[outcome.status] = counts.get(outcome.status, 0) + 1
    with_candidate = sum(1 for o in outcomes.values() if o.attempts)
    return {"wall_seconds": round(wall, 1), "status_counts": counts, "tasks_with_candidate": with_candidate,
            "tasks": {tid: {"status": o.status, "seconds": round(o.seconds, 2), "error": o.error,
                            "attempts": len(o.attempts or [])} for tid, o in sorted(outcomes.items())}}


def build_submission_file(challenges: Path, output: Path, report: Path, workers: int,
                          per_task: float = PER_TASK_SECONDS, global_seconds: float = GLOBAL_SECONDS) -> dict:
    import time
    tasks = load_challenges(challenges)
    start = time.monotonic()
    outcomes = run_tasks(tasks, solve_task_attempts, workers, per_task, global_seconds)
    submission = assemble(tasks, outcomes)
    validate_submission(submission, tasks)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(submission), encoding="utf-8")
    summary = _report(outcomes, time.monotonic() - start)
    write_detail(json.dumps(summary, indent=1), report)
    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("challenges", type=Path)
    parser.add_argument("--output", type=Path, default=Path("submission.json"))
    parser.add_argument("--report", type=Path, default=Path("submission_report.json"))
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--per-task-seconds", type=float, default=PER_TASK_SECONDS)
    parser.add_argument("--global-seconds", type=float, default=GLOBAL_SECONDS)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    workers = args.workers or default_worker_count()
    summary = build_submission_file(args.challenges, args.output, args.report, workers,
                                    args.per_task_seconds, args.global_seconds)
    print_summary([f"submission written and validated: {args.output} ({os.cpu_count()} cpus, {workers} workers)",
                   f"wall {summary['wall_seconds']}s, statuses {summary['status_counts']}",
                   f"tasks with a verified candidate: {summary['tasks_with_candidate']}"], args.report)


if __name__ == "__main__":
    main()
