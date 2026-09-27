"""Unit tests for first-rule admission (ADR 0097, decision 3)."""
from src.curriculum.loader import Task, TrainPair
from src.curriculum.search.sequence.stage_one import (
    MAX_FIRST_STAGE,
    admissible_first_stages,
    is_same_shape_task,
    monotone_fixed_cells,
)

SOURCE = [[0, 5], [5, 0]]
TARGET = [[0, 9], [8, 0]]


def test_monotone_counts_only_changed_cells():
    inter = [[0, 9], [5, 0]]
    assert monotone_fixed_cells(SOURCE, inter, TARGET) == 1


def test_monotone_rejects_a_change_that_is_not_the_target_value():
    inter = [[0, 7], [5, 0]]
    assert monotone_fixed_cells(SOURCE, inter, TARGET) is None


def test_monotone_rejects_a_shape_change():
    assert monotone_fixed_cells(SOURCE, [[0, 5]], TARGET) is None


def test_monotone_of_an_untouched_grid_is_zero():
    assert monotone_fixed_cells(SOURCE, SOURCE, TARGET) == 0


def test_same_shape_task_detection():
    same = Task("t", [TrainPair(SOURCE, TARGET)], [SOURCE])
    diff = Task("t", [TrainPair(SOURCE, [[1]])], [SOURCE])
    assert is_same_shape_task(same)
    assert not is_same_shape_task(diff)


def test_shape_changing_task_has_no_first_stage():
    task = Task("t", [TrainPair(SOURCE, [[1]])], [SOURCE])
    assert admissible_first_stages(task) == []


def test_first_stages_respect_the_limit():
    task = Task("t", [TrainPair(SOURCE, TARGET)], [SOURCE])
    assert len(admissible_first_stages(task, limit=2)) <= 2
    assert MAX_FIRST_STAGE == 10
