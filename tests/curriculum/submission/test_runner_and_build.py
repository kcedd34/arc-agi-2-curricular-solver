import json
import time

from src.curriculum.loader import Task, TrainPair
from src.curriculum.submission.build import assemble, build_submission_file
from src.curriculum.submission.runner import run_tasks


def _task(task_id, size=1):
    grid = [[0] * size]
    return Task(task_id, [TrainPair(grid, grid)], [grid])


def solve_ok(task):
    return [[[[7]]], [[[8]]]]


def solve_slow(task):
    if task.task_id == "slow":
        time.sleep(60)
    return [[[[7]]]]


def solve_raises(task):
    raise RuntimeError("boom")


def test_ok_outcomes():
    tasks = {"a": _task("a"), "b": _task("b")}
    out = run_tasks(tasks, solve_ok, 2, 30, 60)
    assert {o.status for o in out.values()} == {"ok"}
    assert out["a"].attempts == [[[[7]]], [[[8]]]]


def test_error_is_isolated():
    out = run_tasks({"a": _task("a")}, solve_raises, 1, 30, 60)
    assert out["a"].status == "error" and "boom" in out["a"].error


def test_hard_timeout_kills_worker():
    tasks = {"slow": _task("slow"), "fast": _task("fast", 2)}
    out = run_tasks(tasks, solve_slow, 2, 1.5, 60)
    assert out["slow"].status == "timeout" and out["fast"].status == "ok"


def test_global_budget_skips_remaining():
    tasks = {"a": _task("a"), "b": _task("b", 2)}
    out = run_tasks(tasks, solve_ok, 1, 30, 0)
    assert {o.status for o in out.values()} == {"skipped_budget"}


def test_assemble_uses_fallback_for_missing_attempts():
    tasks = {"a": _task("a")}
    out = run_tasks(tasks, solve_raises, 1, 30, 60)
    assert assemble(tasks, out)["a"] == [{"attempt_1": [[0]], "attempt_2": [[0]]}]


def test_build_submission_file_end_to_end(tmp_path):
    raw = {"x": {"train": [{"input": [[1, 2]], "output": [[2, 1]]}, {"input": [[3, 4]], "output": [[4, 3]]}],
                 "test": [{"input": [[5, 6]]}]}}
    challenges = tmp_path / "arc-agi_test_challenges.json"
    challenges.write_text(json.dumps(raw))
    summary = build_submission_file(challenges, tmp_path / "submission.json", tmp_path / "rep.json", 1, 60, 120)
    sub = json.loads((tmp_path / "submission.json").read_text())
    assert set(sub["x"][0]) == {"attempt_1", "attempt_2"}
    assert summary["status_counts"] == {"ok": 1}
