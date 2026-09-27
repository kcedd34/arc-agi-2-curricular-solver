"""Command-line entry point for the curricular-restart workflow.

Thin orchestration only: every subcommand delegates to an already-tested
module (select/state/desk_check/regression/probe/validation); no new
solving, scoring, or persistence logic lives here.

Usage: python -m src.curriculum.cli <subcommand> [args]
"""
import argparse
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

from src.curriculum.cli_output import print_summary, write_detail
from src.curriculum.desk_check.persist import write_desk_check_artifacts
from src.curriculum.desk_check.report import format_report
from src.curriculum.desk_check.run import run_desk_check
from src.curriculum.loader import Task, load_task
from src.curriculum.parallel_batch import add_worker_arguments, resolve_workers
from src.curriculum.probe import DEFAULT_TRAINING_DIR as PROBE_TRAINING_DIR
from src.curriculum.probe import load_probe_pool, run_probe_checkpoint_timed
from src.curriculum.timing_report import timing_line, write_task_times
from src.curriculum.select import DEFAULT_PARTITION_PATH, load_curricular_pool, select_next_task
from src.curriculum.state import CurriculumState, DEFAULT_STATE_PATH, load_state, mark_task_solved, save_state
from src.curriculum.validation import validate_state
from src.curriculum.verified_verdict import compute_verified_verdict

DEFAULT_TASK_DIR = Path("data/ARC-AGI-2/data/training")
PROBE_TIMES_PATH = Path("outputs/curriculum/probe-task-times.json")


def _load_task_by_id(task_id: str, training_dir: Path = DEFAULT_TASK_DIR) -> Task:
    return load_task(training_dir / f"{task_id}.json")


def cmd_next(state: CurriculumState, _args: argparse.Namespace) -> None:
    pool = load_curricular_pool(DEFAULT_PARTITION_PATH)
    next_task = select_next_task(state, pool)
    print(next_task if next_task is not None else "No remaining curricular tasks.")


def cmd_check(_state: CurriculumState, args: argparse.Namespace) -> None:
    task = _load_task_by_id(args.task_id)
    report = run_desk_check(task)
    detail_path = write_detail(
        format_report(report), Path(f"outputs/curriculum/desk-check-reports/{task.task_id}-check.txt")
    )
    print_summary(
        [
            f"Task: {report.task_id}",
            f"Unanimous (not gabarito-verified): {report.unanimous}",
            f"Verified candidates: {len(report.verified)}",
        ],
        detail_path,
    )


def cmd_solve(state: CurriculumState, args: argparse.Namespace) -> None:
    """Acceptance gate. `solved` here means the corrected, gabarito-verified
    verdict from `verified_verdict.py` (RN-CUR-04's two-attempt policy) -
    never desk_check's `unanimous` field, which is candidate-agreement
    only (2026-09-22 correction, after unanimous-but-wrong tasks were
    wrongly accepted: 73ccf9c2, b230c067, f5aa3634)."""
    task = _load_task_by_id(args.task_id)
    report = run_desk_check(task)
    verdict = compute_verified_verdict(args.task_id)
    detail_path = write_detail(
        format_report(report), Path(f"outputs/curriculum/desk-check-reports/{task.task_id}-solve.txt")
    )
    summary = [
        f"Task: {report.task_id}",
        f"Unanimous: {verdict.unanimous}  Solved (gabarito-verified): {verdict.solved}",
        f"Verified candidates: {len(report.verified)}",
    ]

    if verdict.solved:
        updated = mark_task_solved(state, args.task_id, updated_at=str(date.today()))
        save_state(updated, DEFAULT_STATE_PATH)
        summary.append(f"Marked {args.task_id} as solved in {DEFAULT_STATE_PATH}.")

    print_summary(summary, detail_path)


def cmd_desk_check_persist(_state: CurriculumState, args: argparse.Namespace) -> None:
    task = _load_task_by_id(args.task_id)
    report = run_desk_check(task)
    md_path = write_desk_check_artifacts(task, report, solutions_dir=DEFAULT_TASK_DIR)
    print_summary(
        [
            f"Task: {task.task_id}",
            f"Unanimous (not gabarito-verified): {report.unanimous}",
            f"Verified candidates persisted: {len(report.verified)}",
        ],
        md_path,
    )


def cmd_validate(state: CurriculumState, _args: argparse.Namespace) -> None:
    result = validate_state(state)
    lines = [f"SCHEMA ERROR: {error}" for error in result.schema_errors]
    lines += [f"REGRESSION: {task_id} no longer solves" for task_id in result.regression.regressed]
    detail_path = write_detail(
        "\n".join(lines) if lines else "No schema errors or regressions.",
        Path("outputs/curriculum/validation-report.txt"),
    )
    print_summary(
        [
            f"Schema errors: {len(result.schema_errors)}",
            f"Regressions: {len(result.regression.regressed)}",
            "VALID" if result.is_valid else "INVALID",
        ],
        detail_path,
    )


def cmd_probe(state: CurriculumState, args: argparse.Namespace) -> None:
    pool = load_probe_pool()
    workers_used = resolve_workers(args.workers, args.sequential)
    checkpoint, timing = run_probe_checkpoint_timed(
        pool, date=str(date.today()), training_dir=PROBE_TRAINING_DIR, max_workers=workers_used
    )
    updated = state
    updated.probe_pool_checkpoints.append(asdict(checkpoint))
    save_state(updated, DEFAULT_STATE_PATH)
    print_summary(
        [
            f"Probe checkpoint {checkpoint.date}: "
            f"{checkpoint.num_solved}/{checkpoint.num_tasks} solved (gabarito-verified)",
            f"accuracy={checkpoint.accuracy:.4f} unanimous={checkpoint.num_unanimous} "
            f"solved@1={checkpoint.num_solved_at_1} solved@2={checkpoint.num_solved_at_2}",
            f"sequence budget cuts: budget_hit={checkpoint.num_budget_hit} deadline_hit={checkpoint.num_deadline_hit}",
            timing_line(timing, workers_used),
            f"Per-task times: {write_task_times(PROBE_TIMES_PATH, timing)}",
        ],
        DEFAULT_STATE_PATH,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="curriculum-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("next", help="print the next unsolved curricular-pool task id")

    check_parser = subparsers.add_parser("check", help="desk-check a task without changing state")
    check_parser.add_argument("task_id")

    solve_parser = subparsers.add_parser("solve", help="desk-check a task; mark solved in state if solved")
    solve_parser.add_argument("task_id")

    persist_parser = subparsers.add_parser(
        "desk-check-persist", help="run a desk check and persist its artifacts (JSON + markdown) to disk"
    )
    persist_parser.add_argument("task_id")

    subparsers.add_parser("validate", help="run schema + regression checks against the current state")

    probe_parser = subparsers.add_parser("probe", help="run a probe-pool checkpoint and append it to state")
    add_worker_arguments(probe_parser)

    return parser


_COMMANDS = {
    "next": cmd_next,
    "check": cmd_check,
    "solve": cmd_solve,
    "desk-check-persist": cmd_desk_check_persist,
    "validate": cmd_validate,
    "probe": cmd_probe,
}


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    state = load_state(DEFAULT_STATE_PATH)
    _COMMANDS[args.command](state, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
