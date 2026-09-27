from src.evaluation.worst_case_task import find_largest_task
from src.utils.task_loader import Pair, Task


def test_find_largest_task_picks_task_with_most_total_cells():
    small = Task("small", train=[Pair([[0]], [[0]])], test=[Pair([[0]], [[0]])])
    large = Task(
        "large",
        train=[Pair([[0] * 10] * 10, [[0] * 10] * 10)],
        test=[Pair([[0] * 10] * 10, [[0] * 10] * 10)],
    )
    result = find_largest_task({"small": small, "large": large})
    assert result.task_id == "large"


def test_find_largest_task_counts_train_and_test_pairs_together():
    only_train_large = Task(
        "only_train_large",
        train=[Pair([[0] * 5] * 5, [[0] * 5] * 5)],
        test=[Pair([[0]], [[0]])],
    )
    only_test_large = Task(
        "only_test_large",
        train=[Pair([[0]], [[0]])],
        test=[Pair([[0] * 5] * 5, [[0] * 5] * 5)],
    )
    result = find_largest_task({"only_train_large": only_train_large, "only_test_large": only_test_large})
    assert result.task_id in ("only_train_large", "only_test_large")
