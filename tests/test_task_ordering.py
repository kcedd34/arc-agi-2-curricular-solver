from src.evaluation.task_ordering import order_tasks_by_expected_neural_cost
from src.utils.task_loader import Pair, Task


def _task(task_id, train_shapes, test_shapes):
    train = [Pair(input=_grid(rows, cols), output=_grid(rows, cols)) for rows, cols in train_shapes]
    test = [Pair(input=_grid(rows, cols), output=[[0]]) for rows, cols in test_shapes]
    return Task(task_id=task_id, train=train, test=test)


def _grid(rows, cols):
    return [[0] * cols for _ in range(rows)]


def test_orders_ascending_by_total_cell_count():
    tasks = {
        "big": _task("big", [(10, 10)], [(10, 10)]),
        "small": _task("small", [(1, 1)], [(1, 1)]),
        "medium": _task("medium", [(3, 3)], [(3, 3)]),
    }
    assert order_tasks_by_expected_neural_cost(tasks) == ["small", "medium", "big"]


def test_counts_both_train_input_and_output_and_test_input():
    tasks = {
        "wide_train": _task("wide_train", [(1, 100)], [(1, 1)]),
        "wide_test": _task("wide_test", [(1, 1)], [(1, 100)]),
    }
    ordering = order_tasks_by_expected_neural_cost(tasks)
    assert set(ordering) == {"wide_train", "wide_test"}


def test_returns_all_task_ids_exactly_once():
    tasks = {
        "a": _task("a", [(2, 2)], [(2, 2)]),
        "b": _task("b", [(1, 1)], [(1, 1)]),
        "c": _task("c", [(5, 5)], [(5, 5)]),
    }
    ordering = order_tasks_by_expected_neural_cost(tasks)
    assert sorted(ordering) == sorted(tasks)
    assert len(ordering) == len(tasks)
