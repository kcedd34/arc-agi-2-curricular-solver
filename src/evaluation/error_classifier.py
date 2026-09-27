"""Heuristic classification of a task's train-pair transformation type.

Coarse label for error-diagnostic reporting only, never a solving
strategy: spots a dominant failure pattern across tasks, not a certain
answer. Returns NOT_CLASSIFIABLE rather than guessing when no signal
fits.
"""
from src.solvers.color_mapping import infer_color_mapping, same_shape
from src.utils.grid_ops import GEOMETRIC_TRANSFORMS, identity
from src.utils.task_loader import Task

COLOR = "color"
SHAPE_OR_COUNT = "shape/count"
SYMMETRY_OR_ROTATION = "symmetry/rotation"
COMBINATION = "combination"
NOT_CLASSIFIABLE = "not classifiable"


def _has_color_signal(task: Task) -> bool:
    mapping = infer_color_mapping(task.train)
    if mapping is None:
        return False
    return any(source != target for source, target in mapping.items())


def _has_symmetry_signal(task: Task) -> bool:
    non_identity_transforms = [t for t in GEOMETRIC_TRANSFORMS if t is not identity]
    return any(
        all(transform(pair.input) == pair.output for pair in task.train)
        for transform in non_identity_transforms
    )


def _has_shape_or_count_signal(task: Task) -> bool:
    return any(not same_shape(pair.input, pair.output) for pair in task.train)


def classify_task_transform(task: Task) -> str:
    signals = [
        label
        for label, has_signal in (
            (COLOR, _has_color_signal(task)),
            (SYMMETRY_OR_ROTATION, _has_symmetry_signal(task)),
            (SHAPE_OR_COUNT, _has_shape_or_count_signal(task)),
        )
        if has_signal
    ]
    if len(signals) == 0:
        return NOT_CLASSIFIABLE
    if len(signals) == 1:
        return signals[0]
    return COMBINATION
