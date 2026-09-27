import json

from src.evaluation.build_hybrid_submission import build_and_write, run_hybrid_pass
from src.evaluation.time_budget import TimeBudget
from src.utils.task_loader import Pair, Task


def _task(task_id, value):
    train = [Pair(input=[[value]], output=[[value]])]
    test = [Pair(input=[[value]], output=[[0]])]
    return Task(task_id=task_id, train=train, test=test)


def test_run_hybrid_pass_uses_neural_result_when_within_budget():
    tasks = {"t1": _task("t1", 1)}
    budget = TimeBudget(ceiling_seconds=100.0)
    predictions = run_hybrid_pass(tasks, budget, neural_solve=lambda task: [[[9]]])
    assert predictions["t1"] == [[[9]]]


def test_run_hybrid_pass_keeps_symbolic_result_when_budget_already_exhausted():
    tasks = {"t1": _task("t1", 1)}
    budget = TimeBudget(ceiling_seconds=0.0)
    predictions = run_hybrid_pass(tasks, budget, neural_solve=lambda task: [[[9]]])
    assert predictions["t1"] == [[[[1]]]]


def test_run_hybrid_pass_keeps_symbolic_result_when_neural_raises():
    tasks = {"t1": _task("t1", 1)}
    budget = TimeBudget(ceiling_seconds=100.0)

    def failing_neural_solve(task):
        raise RuntimeError("GPU exploded")

    predictions = run_hybrid_pass(tasks, budget, neural_solve=failing_neural_solve)
    assert predictions["t1"] == [[[[1]]]]


def test_run_hybrid_pass_keeps_symbolic_result_when_neural_returns_empty():
    tasks = {"t1": _task("t1", 1)}
    budget = TimeBudget(ceiling_seconds=100.0)
    predictions = run_hybrid_pass(tasks, budget, neural_solve=lambda task: [[]])
    assert predictions["t1"] == [[[[1]]]]


def test_run_hybrid_pass_stops_once_budget_exhausted_mid_pass():
    tasks = {"small": _task("small", 1), "big": _task("big", 2)}
    budget = TimeBudget(ceiling_seconds=10.0)
    calls = []

    def neural_solve(task):
        calls.append(task.task_id)
        budget.record(10.0)
        return [[[9]]]

    predictions = run_hybrid_pass(tasks, budget, neural_solve=neural_solve)
    assert calls == ["small"]
    assert predictions["small"] == [[[9]]]
    assert predictions["big"] == [[[[2]]]]


def test_run_hybrid_pass_processes_ascending_by_expected_cost():
    tasks = {
        "big": Task(
            task_id="big",
            train=[Pair(input=[[0] * 10] * 10, output=[[0] * 10] * 10)],
            test=[Pair(input=[[0] * 10] * 10, output=[[0]])],
        ),
        "small": _task("small", 1),
    }
    budget = TimeBudget(ceiling_seconds=100.0)
    order = []

    def neural_solve(task):
        order.append(task.task_id)
        return [[[9]]]

    run_hybrid_pass(tasks, budget, neural_solve=neural_solve)
    assert order == ["small", "big"]


def test_build_and_write_produces_a_valid_submission_file(tmp_path):
    raw = {
        "t1": {
            "train": [{"input": [[1, 2]], "output": [[2, 1]]}],
            "test": [{"input": [[3, 4]]}],
        }
    }
    challenges_path = tmp_path / "arc-agi_test_challenges.json"
    challenges_path.write_text(json.dumps(raw), encoding="utf-8")
    output_path = tmp_path / "submission.json"

    summary = build_and_write(
        challenges_path,
        output_path,
        neural_solve=lambda task: [[[[5, 5]]]],
        ceiling_seconds=100.0,
    )

    assert summary["task_count"] == 1
    assert output_path.exists()
    submission = json.loads(output_path.read_text(encoding="utf-8"))
    assert submission["t1"][0]["attempt_1"] == [[5, 5]]


def test_build_and_write_falls_back_to_symbolic_when_budget_is_zero(tmp_path):
    raw = {
        "t1": {
            "train": [{"input": [[1, 2]], "output": [[2, 1]]}],
            "test": [{"input": [[3, 4]]}],
        }
    }
    challenges_path = tmp_path / "arc-agi_test_challenges.json"
    challenges_path.write_text(json.dumps(raw), encoding="utf-8")
    output_path = tmp_path / "submission.json"

    summary = build_and_write(
        challenges_path,
        output_path,
        neural_solve=lambda task: [[[9, 9]]],
        ceiling_seconds=0.0,
    )

    assert summary["neural_pass_seconds"] == 0.0
    submission = json.loads(output_path.read_text(encoding="utf-8"))
    assert submission["t1"][0]["attempt_1"] == [[4, 3]]
