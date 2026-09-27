"""Scale test on the training set's largest tasks (object-pack.md Section
5.7): does the promoted library (main + object pack) solve any of the
biggest, most expensive-to-search tasks, and if not, what is the closest
verified hypothesis and what does it miss.

Reuses `search/rank.py::search_task` (now the combined library, RN-CUR-31)
for the solved/unsolved verdict and timing, and
`search/diagnostics.py::build_search_log` for the main-library closest
hypothesis when a task is unsolved (RN-CUR-31: no duplicate enumeration
logic). Object-pack candidate count is read directly from
`library/objects/object_search.py::enumerate_object_compositions` for
transparency on how many object-pack hypotheses were tried.

RN-CUR-32/ADR 0063: full per-task detail to a file, short terminal summary.

2026-09-22 correction: the solved/unsolved verdict used to come from
`search_task(task).status`, which only means unanimous agreement among
verified candidates, not a real gabarito match. Timing and the verdict
now both come from `verified_verdict.compute_verified_verdict`, which
applies RN-CUR-04's two-attempt policy against the real gabarito;
`unanimous` is kept as a separate, non-acceptance field.
"""
import argparse
import functools
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from src.curriculum.cli_output import print_summary, write_detail
from src.curriculum.grid import grids_equal
from src.curriculum.library.objects.object_search import enumerate_object_compositions
from src.curriculum.loader import load_task
from src.curriculum.parallel_batch import add_worker_arguments, resolve_workers, run_batch
from src.curriculum.search.diagnostics import build_search_log
from src.curriculum.solved_split import count_split, format_split
from src.curriculum.timing import summarize_durations
from src.curriculum.timing_report import timing_line, write_task_times
from src.curriculum.verified_verdict import compute_verified_verdict

DEFAULT_TRAINING_DIR = Path("data/ARC-AGI-2/data/training")
DEFAULT_REPORT_PATH = Path("outputs/curriculum/scale-test-v5-detail.txt")
SCALE_TIMES_PATH = Path("outputs/curriculum/scale-task-times.json")

SCALE_TEST_TASK_IDS = ["b74ca5d1", "f9d67f8b", "05a7bcf2", "264363fd", "753ea09b"]


@dataclass
class ScaleTaskResult:
    task_id: str
    unanimous: bool
    solved: bool
    elapsed_s: float
    object_candidates_enumerated: int
    closest_hypothesis: Optional[str]
    closest_cell_similarity: Optional[float]
    error: Optional[str] = None
    solved_at_1: bool = False
    budget_hit: bool = False
    deadline_hit: bool = False


def _cell_similarity(predicted, expected) -> float:
    if predicted is None or expected is None:
        return 0.0
    ph, pw = len(predicted), len(predicted[0]) if predicted else 0
    eh, ew = len(expected), len(expected[0]) if expected else 0
    if (ph, pw) != (eh, ew) or ph == 0:
        return 0.0
    total = ph * pw
    matches = sum(
        1
        for r in range(ph)
        for c in range(pw)
        if predicted[r][c] == expected[r][c]
    )
    return matches / total


def _closest_main_library_hypothesis(task, log) -> (Optional[str], Optional[float]):
    from src.curriculum.search.compose import build_composition_steps
    from src.curriculum.spec import interpreter

    best_desc = None
    best_sim = -1.0
    for candidate_log in log.candidates:
        steps = build_composition_steps(candidate_log.composition)
        sims = []
        for pair in task.train:
            try:
                output_grid, _trace = interpreter.run(steps, pair.input)
            except interpreter.InterpreterError:
                sims.append(0.0)
                continue
            sims.append(_cell_similarity(output_grid, pair.output))
        avg_sim = sum(sims) / len(sims) if sims else 0.0
        if avg_sim > best_sim:
            best_sim = avg_sim
            best_desc = candidate_log.composition.describe()
    return best_desc, (best_sim if best_desc is not None else None)


def _scale_worker(task_id: str, training_dir: Path) -> ScaleTaskResult:
    try:
        task = load_task(training_dir / f"{task_id}.json")

        start = time.time()
        verdict = compute_verified_verdict(task_id, training_dir)
        elapsed = time.time() - start

        object_count = sum(1 for _ in enumerate_object_compositions(task))

        closest_desc = None
        closest_sim = None
        if not verdict.solved:
            log = build_search_log(task)
            closest_desc, closest_sim = _closest_main_library_hypothesis(task, log)

        return ScaleTaskResult(
            task_id=task_id,
            unanimous=verdict.unanimous,
            solved=verdict.solved,
            elapsed_s=elapsed,
            object_candidates_enumerated=object_count,
            closest_hypothesis=closest_desc,
            closest_cell_similarity=closest_sim,
            solved_at_1=verdict.solved_at_1,
            budget_hit=verdict.budget_hit,
            deadline_hit=verdict.deadline_hit,
        )
    except Exception as exc:  # isolated per-task failure, RN-CUR-32 batch discipline
        return ScaleTaskResult(
            task_id=task_id,
            unanimous=False,
            solved=False,
            elapsed_s=0.0,
            object_candidates_enumerated=0,
            closest_hypothesis=None,
            closest_cell_similarity=None,
            error=repr(exc),
        )


def run_scale_test(
    task_ids: List[str] = SCALE_TEST_TASK_IDS,
    training_dir: Path = DEFAULT_TRAINING_DIR,
    max_workers: Optional[int] = None,
) -> List[ScaleTaskResult]:
    worker = functools.partial(_scale_worker, training_dir=training_dir)
    outcomes = run_batch(task_ids, worker, max_workers=max_workers)
    return [
        result if not isinstance(result, BaseException)
        else ScaleTaskResult(
            task_id=task_id, unanimous=False, solved=False, elapsed_s=0.0, object_candidates_enumerated=0,
            closest_hypothesis=None, closest_cell_similarity=None, error=repr(result),
        )
        for task_id, result in outcomes
    ]


def format_report(results: List[ScaleTaskResult]) -> str:
    lines = [
        f"Scale test (v5, object pack promoted): {len(results)} tasks",
        f"Solved: {format_split(count_split(results))} of {len(results)}",
        f"Sequence budget cuts: budget_hit={sum(r.budget_hit for r in results)} "
        f"deadline_hit={sum(r.deadline_hit for r in results)}",
        "",
    ]
    for r in results:
        lines.append(
            f"{r.task_id}: unanimous={r.unanimous} solved={r.solved} at1={r.solved_at_1} time={r.elapsed_s:.4f}s "
            f"object_candidates={r.object_candidates_enumerated}"
        )
        if r.closest_hypothesis is not None:
            lines.append(f"  closest hypothesis: {r.closest_hypothesis} (cell_similarity={r.closest_cell_similarity:.3f})")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    add_worker_arguments(parser)
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    workers_used = resolve_workers(args.workers, args.sequential)
    wall_start = time.perf_counter()
    results = run_scale_test(max_workers=workers_used)
    timing = summarize_durations({r.task_id: r.elapsed_s for r in results}, time.perf_counter() - wall_start)
    write_task_times(SCALE_TIMES_PATH, timing)
    detail_path = write_detail(format_report(results), DEFAULT_REPORT_PATH)
    print_summary(
        [
            f"Scale test: {len(results)} tasks, {format_split(count_split(results))}",
            f"Sequence budget cuts: budget_hit={sum(r.budget_hit for r in results)} "
            f"deadline_hit={sum(r.deadline_hit for r in results)}",
            timing_line(timing, workers_used),
            *[f"  {r.task_id}: solved={r.solved} ({r.elapsed_s:.3f}s)" for r in results],
        ],
        detail_path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
