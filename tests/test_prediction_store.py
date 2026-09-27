from src.evaluation.prediction_store import load_all_predictions, load_predictions, save_predictions


def test_save_then_load_predictions_round_trip(tmp_path):
    predictions_per_pair = [[[1, 2], [3, 4]], [[5, 6]]]
    save_predictions("task_a", predictions_per_pair, tmp_path)
    loaded = load_predictions("task_a", tmp_path)
    assert loaded == predictions_per_pair


def test_load_predictions_returns_none_when_missing(tmp_path):
    assert load_predictions("missing_task", tmp_path) is None


def test_load_all_predictions_reads_every_saved_task(tmp_path):
    save_predictions("task_a", [[[1]]], tmp_path)
    save_predictions("task_b", [[[2]]], tmp_path)
    loaded = load_all_predictions(tmp_path)
    assert loaded == {"task_a": [[[1]]], "task_b": [[[2]]]}


def test_evaluate_solver_persists_predictions_without_rerunning_solver(tmp_path):
    from src.evaluation.harness import evaluate_solver
    from src.utils.task_loader import Pair, Task

    call_count = {"n": 0}

    def counting_solver(task):
        call_count["n"] += 1
        return [[[9, 9]] for _ in task.test]

    tasks = {"t1": Task(task_id="t1", train=[], test=[Pair(input=[[0, 0]], output=[[9, 9]])])}
    evaluate_solver(counting_solver, tasks, predictions_dir=tmp_path)
    assert call_count["n"] == 1

    reloaded = load_predictions("t1", tmp_path)
    assert reloaded == [[[9, 9]]]
    assert call_count["n"] == 1
