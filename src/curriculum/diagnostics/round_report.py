"""Fase A driver: draw a round's rotating sample and run the real
candidate probe over it, persisting raw results for round-<n>.md
(continuous-loop.md Secao 3, Fase A.1/A.3/A.4). RN-CUR-32/ADR 0063:
short terminal summary, full detail to file.
"""
import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import List

from src.curriculum.cli_output import print_summary, write_detail
from src.curriculum.diagnostics.candidate_probe import CandidateProbeResult, run_candidate_probe_timed
from src.curriculum.diagnostics.sampler import DEFAULT_WINDOW_SIZE, round_sample
from src.curriculum.parallel_batch import add_worker_arguments, resolve_workers

DEFAULT_OUTPUT_DIR = Path("outputs/curriculum/rounds")


def output_path(round_number: int, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    return output_dir / f"round-{round_number}-diagnosis.json"


def _summarize(results: List[CandidateProbeResult]) -> dict:
    no_candidate = [r for r in results if r.num_verified_candidates == 0 and r.error is None]
    wrong_candidate = [r for r in results if r.num_verified_candidates > 0 and not r.solved]
    solved_now = [r for r in results if r.solved]
    errored = [r for r in results if r.error is not None]
    cap_hit = [r for r in results if r.main_cap_hit or r.object_cap_hit]
    return {
        "num_tasks": len(results),
        "no_candidate": len(no_candidate),
        "wrong_candidate": len(wrong_candidate),
        "solved_now": [r.task_id for r in solved_now],
        "errored": [r.task_id for r in errored],
        "cap_hit": len(cap_hit),
    }


def run_round_diagnosis(round_number: int, window_size: int = DEFAULT_WINDOW_SIZE, max_workers=None) -> dict:
    sample = round_sample(round_number, window_size=window_size)
    results, timing = run_candidate_probe_timed(sample, max_workers=max_workers)
    summary = _summarize(results)
    payload = {
        "round": round_number,
        "window_size": window_size,
        "sample": sample,
        "results": [asdict(r) for r in results],
        "summary": summary,
        "timing": asdict(timing),
    }
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("round_number", type=int)
    parser.add_argument("--window-size", type=int, default=DEFAULT_WINDOW_SIZE)
    add_worker_arguments(parser)
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    workers_used = resolve_workers(args.workers, args.sequential)

    payload = run_round_diagnosis(args.round_number, window_size=args.window_size, max_workers=workers_used)

    out_path = output_path(args.round_number)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    summary = payload["summary"]
    timing = payload["timing"]
    detail_path = write_detail(json.dumps(payload, indent=2, ensure_ascii=False), out_path.with_suffix(".detail.json"))
    print_summary(
        [
            f"Round {args.round_number} diagnosis: {summary['num_tasks']} tasks (workers={workers_used})",
            f"no_candidate={summary['no_candidate']} wrong_candidate={summary['wrong_candidate']} "
            f"cap_hit={summary['cap_hit']} errored={len(summary['errored'])}",
            f"solved_now (unexpected, worth checking): {summary['solved_now']}",
            f"wall={timing['wall_seconds']:.1f}s mean={timing['mean_task_seconds']:.2f}s "
            f"median={timing['median_task_seconds']:.2f}s max={timing['max_task_seconds']:.1f}s "
            f"({timing['slowest_task_id'] or '-'}) n={timing['num_timed']}",
            f"Saved to {out_path}",
        ],
        detail_path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
