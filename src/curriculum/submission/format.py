"""Builds and validates submission.json entries, per ADR 0006."""
from typing import Dict, List, Optional

from src.curriculum.grid import Grid, is_valid_grid
from src.curriculum.loader import Task
from src.curriculum.submission.fallback import fallback_attempt_1, fallback_attempt_2


def build_entries(task: Task, attempts: Optional[List[List[Grid]]]) -> List[dict]:
    """One {attempt_1, attempt_2} entry per test input, order preserved."""
    attempts = attempts or []
    return [_build_entry(task, index, attempts) for index in range(len(task.test_inputs))]


def _build_entry(task: Task, index: int, attempts: List[List[Grid]]) -> dict:
    first = _attempt_grid(attempts, 0, index)
    if first is None:
        first = fallback_attempt_1(task.test_inputs[index])
        second = fallback_attempt_2([p.output for p in task.train], first)
        return {"attempt_1": first, "attempt_2": second}
    second = _attempt_grid(attempts, 1, index)
    return {"attempt_1": first, "attempt_2": first if second is None else second}


def _attempt_grid(attempts: List[List[Grid]], attempt: int, index: int) -> Optional[Grid]:
    if attempt >= len(attempts) or index >= len(attempts[attempt]):
        return None
    grid = attempts[attempt][index]
    return grid if is_valid_grid(grid) else None


def validate_submission(submission: Dict[str, List[dict]], tasks: Dict[str, Task]) -> None:
    missing = set(tasks) - set(submission)
    extra = set(submission) - set(tasks)
    if missing or extra:
        raise ValueError(f"task_id mismatch: missing={sorted(missing)} extra={sorted(extra)}")
    for task_id, task in tasks.items():
        _validate_entries(task_id, submission[task_id], len(task.test_inputs))


def _validate_entries(task_id: str, entries: List[dict], expected: int) -> None:
    if len(entries) != expected:
        raise ValueError(f"task {task_id}: expected {expected} entries, got {len(entries)}")
    for entry in entries:
        if set(entry) != {"attempt_1", "attempt_2"}:
            raise ValueError(f"task {task_id}: entry keys must be attempt_1/attempt_2, got {set(entry)}")
        for grid in entry.values():
            if not (isinstance(grid, list) and is_valid_grid(grid) and _all_int(grid)):
                raise ValueError(f"task {task_id}: invalid grid {grid!r}")


def _all_int(grid: Grid) -> bool:
    return all(type(cell) is int for row in grid for cell in row)
