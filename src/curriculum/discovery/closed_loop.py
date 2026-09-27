"""Closed discovery loop (ADR 0110): batches over the arc2_only training tasks,
no human in the loop. `python -m src.curriculum.discovery.closed_loop`."""
import argparse
import json
import os
import sys
from typing import List

from src.curriculum.cli_output import print_summary
from src.curriculum.discovery.library_store import LIBRARY_DIR
from src.curriculum.discovery.loop_batches import credit_registry, run_frozen_batch, snapshot_name, split_batches
from src.curriculum.discovery.loop_report import build_report, summary_lines, write_report
from src.curriculum.discovery.loop_scoring import score_run
from src.curriculum.discovery.loop_tasks import arc2_only_task_ids, taught_task_ids
from src.curriculum.discovery.registry import Registry
from src.curriculum.discovery.run_task import TaskRun
from src.curriculum.discovery.switch import ENV_VAR
from src.curriculum.discovery.task_generated import _entries
from src.curriculum.parallel_batch import add_worker_arguments, resolve_workers

BUILD_REPORT = LIBRARY_DIR / "build-report-stride10-depth3.json"


def _hit_row(hit) -> dict:
    return {
        "text": hit.description, "generated": hit.uses_generated, "accepted": hit.accepted,
        "reasons": hit.reasons, "positions": hit.positions,
    }


def _trace_lines(runs: List[TaskRun], batch: int) -> List[dict]:
    return [
        {"batch": batch, "task": r.task_id, "profile": r.profile, "seconds": round(r.seconds, 1),
         "units": r.units, "error": r.error, "hits": [_hit_row(h) for h in r.hits]}
        for r in runs
    ]


def run_loop(task_ids: List[str], batch_size: int, workers: int, prefix: str):
    registry, batches, trace = Registry(len(_entries())), [], []
    for number, ids in enumerate(split_batches(task_ids, batch_size), start=1):
        runs = run_frozen_batch(ids, registry, workers)
        batches.append(runs)
        trace += _trace_lines(runs, number)
        credit_registry(registry, runs)
        registry.save(snapshot_name(prefix, number))
        print(f"batch {number} done ({len(ids)} tasks)", flush=True)
    return registry, batches, trace


def _finish(registry, batches, trace, prefix: str) -> None:
    runs = [r for batch in batches for r in batch]
    scores = {r.task_id: score_run(r) for r in runs}
    stats = json.loads(BUILD_REPORT.read_text(encoding="utf-8"))["stats"]
    report = build_report(runs, scores, taught_task_ids(), stats, registry, batches)
    detail = LIBRARY_DIR / f"{prefix}-report.json"
    write_report(report, detail)
    (LIBRARY_DIR / f"{prefix}-trace.json").write_text(json.dumps(trace), encoding="utf-8")
    print_summary(summary_lines(report), detail)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=24)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--prefix", default="loop-r22")
    add_worker_arguments(parser)
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    os.environ[ENV_VAR] = "1"
    ids = arc2_only_task_ids()[: args.limit or None]
    registry, batches, trace = run_loop(ids, args.batch_size, resolve_workers(args.workers, args.sequential), args.prefix)
    _finish(registry, batches, trace, args.prefix)
    return 0


if __name__ == "__main__":
    sys.exit(main())
