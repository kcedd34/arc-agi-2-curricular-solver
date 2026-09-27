from src.evaluation.error_classifier import (
    COLOR,
    COMBINATION,
    NOT_CLASSIFIABLE,
    SHAPE_OR_COUNT,
    SYMMETRY_OR_ROTATION,
    classify_task_transform,
)
from src.utils.task_loader import Pair, Task


def test_color_only_task():
    task = Task(task_id="t1", train=[Pair(input=[[1, 2]], output=[[2, 3]])], test=[])
    assert classify_task_transform(task) == COLOR


def test_symmetry_only_task():
    # Two train pairs so a coincidental single-pair color bijection
    # cannot also explain the transform (rotate90 fits both).
    task = Task(
        task_id="t2",
        train=[
            Pair(input=[[1, 2], [3, 4]], output=[[3, 1], [4, 2]]),
            Pair(input=[[1, 1], [2, 2]], output=[[2, 1], [2, 1]]),
        ],
        test=[],
    )
    assert classify_task_transform(task) == SYMMETRY_OR_ROTATION


def test_shape_or_count_only_task():
    task = Task(task_id="t3", train=[Pair(input=[[1, 2]], output=[[1, 2, 3]])], test=[])
    assert classify_task_transform(task) == SHAPE_OR_COUNT


def test_combination_task():
    # rotate90 of a non-square grid changes both shape and layout: a
    # symmetry match that also trips the shape/count signal.
    task = Task(
        task_id="t4",
        train=[Pair(input=[[1, 2]], output=[[1], [2]])],
        test=[],
    )
    assert classify_task_transform(task) == COMBINATION


def test_not_classifiable_task():
    task = Task(
        task_id="t5",
        train=[Pair(input=[[1, 1], [2, 2]], output=[[5, 6], [2, 9]])],
        test=[],
    )
    assert classify_task_transform(task) == NOT_CLASSIFIABLE
