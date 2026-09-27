"""Builds submission.json using the time-budgeted hybrid pipeline (ADR 0049).

Runs the symbolic solver across every task first (fast, guarantees a
fallback answer per ADR 0011), then attempts the neural solver on tasks in
ascending expected-cost order (`task_ordering.py`) until the neural pass
time budget (`time_budget.py`) is exhausted. Tasks the neural pass does not
reach, or that raise an exception, or that return an empty prediction, keep
their symbolic answer.
"""
import argparse
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

from src.evaluation.submission_format import (
    build_submission_from_predictions,
    validate_submission,
    write_submission,
)
from src.evaluation.task_ordering import order_tasks_by_expected_neural_cost
from src.evaluation.time_budget import NEURAL_PASS_CEILING_SECONDS, TimeBudget
from src.solvers.baseline_solver import solve_task as symbolic_solve_task
from src.utils.grid_types import Grid
from src.utils.kaggle_io import load_challenges
from src.utils.task_loader import Task

NeuralSolve = Callable[[Task], List[List[Grid]]]


def run_hybrid_pass(tasks: Dict[str, Task], budget: TimeBudget, neural_solve: NeuralSolve) -> Dict[str, List[List[Grid]]]:
    predictions = {task_id: symbolic_solve_task(task) for task_id, task in tasks.items()}
    for task_id in order_tasks_by_expected_neural_cost(tasks):
        if budget.is_exhausted():
            break
        neural_predictions = _attempt_neural_task(tasks[task_id], neural_solve, budget)
        if neural_predictions is not None and all(neural_predictions):
            predictions[task_id] = neural_predictions
    return predictions


def _attempt_neural_task(task: Task, neural_solve: NeuralSolve, budget: TimeBudget) -> Optional[List[List[Grid]]]:
    start = budget.clock()
    try:
        result = neural_solve(task)
    except Exception:
        result = None
    finally:
        budget.record(budget.clock() - start)
    return result


def build_and_write(
    challenges_path: Path,
    output_path: Path,
    neural_solve: NeuralSolve,
    ceiling_seconds: float = NEURAL_PASS_CEILING_SECONDS,
) -> dict:
    tasks = load_challenges(challenges_path)
    budget = TimeBudget(ceiling_seconds=ceiling_seconds)

    start = time.monotonic()
    predictions = run_hybrid_pass(tasks, budget, neural_solve)
    elapsed = time.monotonic() - start

    submission = build_submission_from_predictions(predictions, tasks)
    validate_submission(submission, tasks)
    write_submission(submission, output_path)

    return {
        "task_count": len(tasks),
        "elapsed_seconds": elapsed,
        "neural_pass_seconds": budget.elapsed_seconds(),
        "output_path": str(output_path),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("challenges_path", type=Path, help="path to the official *_challenges.json file")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("submission.json"),
        help="where to write submission.json (default: ./submission.json)",
    )
    parser.add_argument(
        "--ceiling-seconds",
        type=float,
        default=NEURAL_PASS_CEILING_SECONDS,
        help="neural pass wall-clock ceiling in seconds (default: ADR 0049's ~8h)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    from src.solvers.neural_solver import solve_task as neural_solve_task

    summary = build_and_write(args.challenges_path, args.output, neural_solve_task, args.ceiling_seconds)
    print(
        f"OK: {summary['task_count']} tasks solved and validated in "
        f"{summary['elapsed_seconds']:.2f}s (neural pass: "
        f"{summary['neural_pass_seconds']:.2f}s) -> {summary['output_path']}"
    )


if __name__ == "__main__":
    main()
