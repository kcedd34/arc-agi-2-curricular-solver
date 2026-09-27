"""Orders tasks for the time-budgeted neural pass (ADR 0049): ascending by
total grid cell count across a task's train pairs and test inputs, a cheap
proxy for neural solve cost that needs no GPU to compute, so the budget
favors fitting more tasks rather than being consumed early by a handful of
large ones. ADR 0028 found neural generation time is not strictly
proportional to grid size, so this is a heuristic, not a precise estimate.
"""
from typing import Dict, List

from src.utils.task_loader import Task


def _grid_cells(grid) -> int:
    return len(grid) * len(grid[0]) if grid else 0


def _task_total_cells(task: Task) -> int:
    train_cells = sum(_grid_cells(pair.input) + _grid_cells(pair.output) for pair in task.train)
    test_cells = sum(_grid_cells(pair.input) for pair in task.test)
    return train_cells + test_cells


def order_tasks_by_expected_neural_cost(tasks: Dict[str, Task]) -> List[str]:
    return sorted(tasks, key=lambda task_id: _task_total_cells(tasks[task_id]))
