from src.solvers.baseline_solver import predict_test_input
from src.utils.task_loader import Pair, Task


def test_identity_task_is_solved():
    task = Task(
        task_id="t1",
        train=[Pair(input=[[1, 2]], output=[[1, 2]])],
        test=[Pair(input=[[3, 4]], output=[[3, 4]])],
    )
    predictions = predict_test_input(task, [[3, 4]])
    assert [[3, 4]] in predictions


def test_rotation_task_is_solved():
    task = Task(
        task_id="t2",
        train=[Pair(input=[[1, 2], [3, 4]], output=[[3, 1], [4, 2]])],
        test=[Pair(input=[[5, 6], [7, 8]], output=[[7, 5], [8, 6]])],
    )
    predictions = predict_test_input(task, [[5, 6], [7, 8]])
    assert [[7, 5], [8, 6]] in predictions


def test_color_mapping_task_is_solved():
    task = Task(
        task_id="t3",
        train=[Pair(input=[[1, 2]], output=[[2, 3]])],
        test=[Pair(input=[[1, 1]], output=[[2, 2]])],
    )
    predictions = predict_test_input(task, [[1, 1]])
    assert [[2, 2]] in predictions


def test_unsolvable_task_returns_no_correct_prediction():
    task = Task(
        task_id="t4",
        train=[Pair(input=[[1, 2], [3, 4]], output=[[9, 9], [9, 9]])],
        test=[Pair(input=[[5, 6], [7, 8]], output=[[0, 0], [0, 0]])],
    )
    predictions = predict_test_input(task, [[5, 6], [7, 8]])
    assert [[0, 0], [0, 0]] not in predictions
