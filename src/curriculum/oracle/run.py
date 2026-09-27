"""Oracle CLI (diagnostic only, ADR 0111):
`python -m src.curriculum.oracle.run [--limit N] [--tasks a,b] [--workers N]`.
Not imported by the solver, the submission builder or the discovery engine."""
import argparse
import json
import os
import sys
from pathlib import Path

from src.curriculum.cli_output import print_summary
from src.curriculum.discovery.loop_tasks import arc2_only_task_ids
from src.curriculum.discovery.switch import ENV_VAR
from src.curriculum.oracle.report import summarize, summary_lines
from src.curriculum.oracle.verdict import Verdict, assess_id
from src.curriculum.parallel_batch import add_worker_arguments, resolve_workers, run_batch

OUT_DIR = Path("outputs/curriculum/oracle")


def _verdict(task_id: str, outcome) -> Verdict:
    if isinstance(outcome, BaseException):
        return Verdict(task_id, 0.0, 0, 0, False, False, "", f"{type(outcome).__name__}: {outcome}")
    return outcome


def _parse(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--tasks", default="")
    parser.add_argument("--tag", default="r23")
    add_worker_arguments(parser)
    return parser.parse_args(argv)


def _task_ids(args) -> list:
    ids = [t for t in args.tasks.split(",") if t] or arc2_only_task_ids()
    return ids[: args.limit] if args.limit else ids


def main(argv=None) -> int:
    args = _parse(argv if argv is not None else sys.argv[1:])
    os.environ[ENV_VAR] = "1"
    ids = _task_ids(args)
    outcomes = run_batch(ids, assess_id, resolve_workers(args.workers, args.sequential))
    verdicts = [_verdict(task_id, out) for task_id, out in outcomes]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = OUT_DIR / f"oracle-{args.tag}.json"
    summary = summarize(verdicts)
    report.write_text(json.dumps({"summary": summary, "verdicts": [v._asdict() for v in verdicts]}, indent=1), encoding="utf-8")
    print_summary(summary_lines(summary), report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
