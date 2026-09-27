from src.evaluation.error_report import build_error_report
from src.evaluation.prediction_store import load_predictions
from src.utils.task_loader import Pair, Task


GRID = [[9, 9]]


def test_build_error_report_persists_predictions_without_rerunning_solver(tmp_path):
    call_count = {"n": 0}

    def counting_solver(task):
        call_count["n"] += 1
        return [[GRID] for _ in task.test]

    tasks = {"t1": Task(task_id="t1", train=[], test=[Pair(input=[[0, 0]], output=GRID)])}

    reports = build_error_report(counting_solver, tasks, predictions_dir=tmp_path)
    assert call_count["n"] == 1
    assert reports[0].dimension_match is True

    reloaded = load_predictions("t1", tmp_path)
    assert reloaded == [[GRID]]
    assert call_count["n"] == 1


def test_build_error_report_without_predictions_dir_does_not_persist(tmp_path):
    tasks = {"t1": Task(task_id="t1", train=[], test=[Pair(input=[[0, 0]], output=GRID)])}
    build_error_report(lambda task: [[GRID] for _ in task.test], tasks)
    assert load_predictions("t1", tmp_path) is None
