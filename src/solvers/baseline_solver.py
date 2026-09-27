"""Trivial baseline: geometry (identity/rotations/flips) + color mapping.

Only serves to validate the pipeline end to end (kept as a fallback layer
per ADR 0001/ADR 0003 once the neural solver is implemented).
"""
from typing import Callable, List, Optional

from src.solvers.color_mapping import apply_color_mapping, infer_color_mapping
from src.utils.grid_ops import GEOMETRIC_TRANSFORMS
from src.utils.grid_types import Grid
from src.utils.task_loader import Task

MAX_PREDICTIONS = 2


def _transform_fits_all_train_pairs(transform: Callable[[Grid], Grid], task: Task) -> bool:
    return all(transform(pair.input) == pair.output for pair in task.train)


def _find_matching_geometric_transforms(task: Task) -> List[Callable[[Grid], Grid]]:
    return [t for t in GEOMETRIC_TRANSFORMS if _transform_fits_all_train_pairs(t, task)]


def _color_mapping_candidate(task: Task) -> Optional[dict]:
    return infer_color_mapping(task.train)


def predict_test_input(task: Task, test_input: Grid) -> List[Grid]:
    predictions: List[Grid] = []

    for transform in _find_matching_geometric_transforms(task):
        candidate = transform(test_input)
        if candidate not in predictions:
            predictions.append(candidate)
        if len(predictions) >= MAX_PREDICTIONS:
            return predictions[:MAX_PREDICTIONS]

    mapping = _color_mapping_candidate(task)
    if mapping is not None:
        candidate = apply_color_mapping(test_input, mapping)
        if candidate not in predictions:
            predictions.append(candidate)

    return predictions[:MAX_PREDICTIONS]


def solve_task(task: Task) -> List[List[Grid]]:
    return [predict_test_input(task, pair.input) for pair in task.test]
