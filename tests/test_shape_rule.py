from src.solvers.neural.shape_rule import output_shape_equals_input_shape
from src.utils.task_loader import Pair, Task


def _task(train_pairs):
    return Task(task_id="t", train=train_pairs, test=[])


def test_true_when_every_train_pair_output_matches_input_shape():
    task = _task([
        Pair(input=[[1, 2], [3, 4]], output=[[5, 6], [7, 8]]),
        Pair(input=[[1, 2, 3]], output=[[9, 9, 9]]),
    ])
    assert output_shape_equals_input_shape(task) is True


def test_false_when_one_pair_has_a_different_row_count():
    task = _task([
        Pair(input=[[1, 2], [3, 4]], output=[[5, 6], [7, 8]]),
        Pair(input=[[1, 2], [3, 4]], output=[[5, 6]]),
    ])
    assert output_shape_equals_input_shape(task) is False


def test_false_when_one_pair_has_a_different_column_count():
    task = _task([
        Pair(input=[[1, 2], [3, 4]], output=[[5, 6], [7, 8]]),
        Pair(input=[[1, 2]], output=[[5, 6, 7]]),
    ])
    assert output_shape_equals_input_shape(task) is False


def test_true_for_a_single_train_pair():
    task = _task([Pair(input=[[1]], output=[[2]])])
    assert output_shape_equals_input_shape(task) is True
