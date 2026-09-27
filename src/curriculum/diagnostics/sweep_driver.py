"""Scale sweep driver (ADR 0093): runs `build_sweep_record` over the whole
training set (curricular + probe pool) and writes one JSON with a record
per task. Terminal output is a short summary (RN-CUR-32)."""
import argparse
import functools
import json
import sys
import time
from pathlib import Path
from typing import List

from src.curriculum.cli_output import print_summary
from src.curriculum.diagnostics.sweep_record import DEFAULT_TRAINING_DIR, SweepRecord, build_sweep_record
from src.curriculum.parallel_batch import add_worker_arguments, resolve_workers, run_batch
from src.curriculum.timing import TimedResult, summarize_timing, with_timing
from src.curriculum.timing_report import timing_line

DEFAULT_OUT_PATH = Path("outputs/curriculum/diagnostics/sweep.json")


def all_task_ids(training_dir: Path = DEFAULT_TRAINING_DIR) -> List[str]:
    return sorted(p.stem for p in training_dir.glob("*.json"))


def _worker(task_id: str, training_dir: Path) -> SweepRecord:
    return build_sweep_record(task_id, training_dir)


def run_sweep(task_ids: List[str], workers: int, training_dir: Path = DEFAULT_TRAINING_DIR):
    worker = with_timing(functools.partial(_worker, training_dir=training_dir))
    start = time.perf_counter()
    outcomes = run_batch(task_ids, worker, max_workers=workers)
    timing = summarize_timing(outcomes, time.perf_counter() - start)
    records = [
        o.value if isinstance(o, TimedResult) else SweepRecord(task_id=tid, error=repr(o))
        for tid, o in outcomes
    ]
    return records, timing


def write_records(records: List[SweepRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump({r.task_id: r.to_dict() for r in records}, f, indent=1)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    add_worker_arguments(parser)
    parser.add_argument("--limit", type=int, default=None, help="only the first N ids (smoke test)")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    workers = resolve_workers(args.workers, args.sequential)
    task_ids = all_task_ids()[: args.limit]
    records, timing = run_sweep(task_ids, workers)
    write_records(records, DEFAULT_OUT_PATH)
    solved = sum(r.solved for r in records)
    with_cand = sum(r.num_candidates > 0 for r in records)
    errors = sum(r.error is not None for r in records)
    print_summary(
        [
            f"Swept {len(records)} tasks (workers={workers}): candidates>0: {with_cand}, solved: {solved}, errors: {errors}",
            timing_line(timing, workers),
        ],
        DEFAULT_OUT_PATH,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
