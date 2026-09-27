"""Round probe measurement split by origin (ADR 0100): arc2_only FIRST, then
inherited, then total, each with and without the tasks already seen in
earlier rounds. Per-task detail goes to a file; the terminal gets
aggregates only (RN-CUR-05, RN-CUR-32)."""
import argparse
import json
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Dict, List, Set

from src.curriculum.cli_output import print_summary
from src.curriculum.diagnostics.origin import EXCLUSIVE, load_arc1_ids, origin_of
from src.curriculum.parallel_batch import add_worker_arguments, resolve_workers
from src.curriculum.probe import (
    ProbeTaskResult, _checkpoint_from_task_results, load_probe_pool, run_probe_detail_timed,
)
from src.curriculum.state import DEFAULT_STATE_PATH, load_state, save_state
from src.curriculum.timing_report import timing_line, write_task_times

SEEN_ARC2_ONLY = {
    "f0100645", "342dd610", "5b37cb25",
    # hand-solved in Round 18-20 (docs/curriculum/handsolved/): acceptance, never unseen
    "458e3a53", "5a719d11", "7acdf6d3", "981add89",
    "83eb0a57", "b74ca5d1", "e734a0e8", "320afe60", "538b439f", "9f41bd9c",
    "1b59e163", "17b866bd", "3d588dc9", "2ccd9fef", "c3fa4749", "db615bd4",
}
SEEN_ANY = SEEN_ARC2_ONLY | {"6ad5bdfd"}
OUT_DIR = Path("outputs/curriculum/rounds")


def _count(results: List[ProbeTaskResult]) -> Dict[str, int]:
    solved = [r for r in results if r.solved]
    at1 = sum(1 for r in solved if r.solved_at_1)
    return {"n": len(results), "solved": len(solved), "at1": at1, "at2": len(solved) - at1}


def _line(name: str, results: List[ProbeTaskResult], skip: Set[str]) -> str:
    with_seen, without = _count(results), _count([r for r in results if r.task_id not in skip])
    return (f"{name}: {with_seen['solved']}/{with_seen['n']} (@1 {with_seen['at1']}, @2 {with_seen['at2']}) "
            f"with seen | {without['solved']}/{without['n']} (@1 {without['at1']}, @2 {without['at2']}) without")


def origin_groups(results: List[ProbeTaskResult]):
    arc1 = load_arc1_ids()
    arc2 = [r for r in results if origin_of(r.task_id, arc1) == EXCLUSIVE]
    inherited = [r for r in results if origin_of(r.task_id, arc1) != EXCLUSIVE]
    return arc2, inherited


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("round_number", type=int)
    add_worker_arguments(parser)
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    workers = resolve_workers(args.workers, args.sequential)
    pool = load_probe_pool()
    results, timing = run_probe_detail_timed(pool, max_workers=workers)
    arc2, inherited = origin_groups(results)
    checkpoint = _checkpoint_from_task_results(pool, str(date.today()), results)
    state = load_state(DEFAULT_STATE_PATH)
    state.probe_pool_checkpoints.append(asdict(checkpoint))
    save_state(state, DEFAULT_STATE_PATH)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    detail = OUT_DIR / f"round-{args.round_number}-probe-detail.json"
    payload = {"inherited": [asdict(r) for r in inherited], "arc2_only_aggregate": _count(arc2)}
    detail.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print_summary([
        _line("arc2_only", arc2, SEEN_ARC2_ONLY),
        _line("inherited", inherited, set()),
        _line("total", results, SEEN_ANY),
        f"Pool sonda: {checkpoint.num_solved}/{checkpoint.num_tasks} (@1 {checkpoint.num_solved_at_1}, @2 {checkpoint.num_solved_at_2})",
        f"sequence budget cuts: budget_hit={checkpoint.num_budget_hit} deadline_hit={checkpoint.num_deadline_hit}",
        timing_line(timing, workers),
        f"Per-task times: {write_task_times(Path('outputs/curriculum/rounds') / f'round-{args.round_number}-probe-times.json', timing)}",
    ], detail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
