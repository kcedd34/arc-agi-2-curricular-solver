"""Selects the task with the largest total grid cell count in a split, used
to smoke-test worst-case GPU memory usage (all train+test pairs share the
same TTT context, so total cells across pairs is the relevant size, not any
single pair's grid).
"""
from typing import Dict

from src.utils.task_loader import Task


def _grid_cells(grid) -> int:
    return len(grid) * len(grid[0])


def _task_total_cells(task: Task) -> int:
    total = 0
    for pair in [*task.train, *task.test]:
        total += _grid_cells(pair.input) + _grid_cells(pair.output)
    return total


def find_largest_task(tasks: Dict[str, Task]) -> Task:
    return max(tasks.values(), key=_task_total_cells)
