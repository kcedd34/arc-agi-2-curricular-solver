import json

import pytest

from src.evaluation.pretraining_split import (
    assert_disjoint_from_reserved_tasks,
    save_split_manifest,
    select_pretraining_tasks,
    select_pretraining_tasks_excluding_reserved,
)
from src.utils.task_loader import Pair, Task


def _fake_tasks(n: int) -> dict:
    return {
        f"task_{i:04d}": Task(task_id=f"task_{i:04d}", train=[Pair(input=[[i]], output=[[i]])], test=[])
        for i in range(n)
    }


def test_select_pretraining_tasks_is_deterministic_for_a_fixed_seed():
    tasks = _fake_tasks(50)
    first = select_pretraining_tasks(tasks, size=10, seed=123)
    second = select_pretraining_tasks(tasks, size=10, seed=123)
    assert list(first.keys()) == list(second.keys())


def test_select_pretraining_tasks_respects_requested_size():
    tasks = _fake_tasks(50)
    selected = select_pretraining_tasks(tasks, size=15, seed=1)
    assert len(selected) == 15


def test_select_pretraining_tasks_caps_at_available_population():
    tasks = _fake_tasks(5)
    selected = select_pretraining_tasks(tasks, size=100, seed=1)
    assert len(selected) == 5


def test_select_pretraining_tasks_different_seeds_give_different_samples():
    tasks = _fake_tasks(50)
    a = set(select_pretraining_tasks(tasks, size=10, seed=1).keys())
    b = set(select_pretraining_tasks(tasks, size=10, seed=2).keys())
    assert a != b


def test_assert_disjoint_from_reserved_tasks_raises_on_overlap():
    with pytest.raises(ValueError):
        assert_disjoint_from_reserved_tasks({"a", "b"}, {"b", "c"})


def test_assert_disjoint_from_reserved_tasks_passes_when_no_overlap():
    assert_disjoint_from_reserved_tasks({"a", "b"}, {"c", "d"}) is None


def test_select_pretraining_tasks_excluding_reserved_raises_if_overlap_present():
    tasks = _fake_tasks(10)
    reserved = {"task_0003"}
    with pytest.raises(ValueError):
        # size=10 forces every task to be picked, including the reserved one.
        select_pretraining_tasks_excluding_reserved(tasks, size=10, reserved_task_ids=reserved, seed=1)


def test_select_pretraining_tasks_excluding_reserved_succeeds_when_disjoint():
    tasks = _fake_tasks(10)
    selected = select_pretraining_tasks_excluding_reserved(tasks, size=5, reserved_task_ids={"not_a_task"}, seed=1)
    assert len(selected) == 5


def test_save_split_manifest_writes_sorted_task_ids(tmp_path):
    manifest_path = tmp_path / "pilot" / "manifest.json"
    save_split_manifest(["b", "a", "c"], manifest_path)
    assert json.loads(manifest_path.read_text()) == ["a", "b", "c"]
