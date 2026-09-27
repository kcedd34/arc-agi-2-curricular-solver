"""Builds and validates the official submission.json format, per ADR 0006."""
import json
from pathlib import Path
from typing import Dict, List

from src.evaluation.harness import Solver
from src.evaluation.submission_fallback import fallback_attempt_1, fallback_attempt_2
from src.utils.grid_types import Grid
from src.utils.task_loader import Pair, Task


def build_submission(solver: Solver, tasks: Dict[str, Task]) -> dict:
    predictions = {task_id: solver(task) for task_id, task in tasks.items()}
    return build_submission_from_predictions(predictions, tasks)


def build_submission_from_predictions(predictions: Dict[str, List[List[Grid]]], tasks: Dict[str, Task]) -> dict:
    """Same as `build_submission`, but takes already-computed predictions.

    Used by the hybrid pipeline (ADR 0049), which builds predictions in two
    passes (symbolic baseline, then a time-budgeted neural upgrade) instead
    of a single `Solver` call per task.
    """
    return {
        task_id: [
            _build_attempt_pair(task_predictions, test_pair, task.train)
            for task_predictions, test_pair in zip(predictions[task_id], task.test)
        ]
        for task_id, task in tasks.items()
    }


def _build_attempt_pair(predictions: List[Grid], test_pair: Pair, train: List[Pair]) -> dict:
    if not predictions:
        attempt_1 = fallback_attempt_1(test_pair)
        attempt_2 = fallback_attempt_2(train, attempt_1)
    else:
        attempt_1 = predictions[0]
        attempt_2 = predictions[1] if len(predictions) > 1 else attempt_1
    return {"attempt_1": attempt_1, "attempt_2": attempt_2}


def validate_submission(submission: dict, tasks: Dict[str, Task]) -> None:
    missing = set(tasks) - set(submission)
    if missing:
        raise ValueError(f"submission missing task_id(s): {sorted(missing)}")
    for task_id, task in tasks.items():
        _validate_task_entries(task_id, submission[task_id], expected_count=len(task.test))


def _validate_task_entries(task_id: str, entries: List[dict], expected_count: int) -> None:
    if len(entries) != expected_count:
        raise ValueError(
            f"task {task_id}: expected {expected_count} test entries, got {len(entries)}"
        )
    for entry in entries:
        if set(entry) != {"attempt_1", "attempt_2"}:
            raise ValueError(f"task {task_id}: entry must have exactly attempt_1/attempt_2, got {set(entry)}")
        for grid in entry.values():
            _validate_grid(task_id, grid)


def _validate_grid(task_id: str, grid) -> None:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError(f"task {task_id}: grid must be a non-empty list of lists, got {grid!r}")
    row_length = len(grid[0])
    for row in grid:
        if len(row) != row_length:
            raise ValueError(f"task {task_id}: grid rows must all have the same length")
        if not all(isinstance(cell, int) and 0 <= cell <= 9 for cell in row):
            raise ValueError(f"task {task_id}: grid cells must be integers 0-9")


def write_submission(submission: dict, output_path: Path) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(submission, f)
