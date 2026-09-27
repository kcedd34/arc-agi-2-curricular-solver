"""The utility registry only reorders: promoted first, dormant last, nothing
dropped, deterministic, reactivation on a hit (ADR 0110)."""
import numpy as np

from src.curriculum.discovery import registry as reg
from src.curriculum.discovery.registry import Registry, load_registry

SIZE = 50


def test_fresh_registry_keeps_library_order():
    assert list(Registry(SIZE).ordered_indices("11111")) == list(range(SIZE))


def test_hits_promote_and_profile_hits_come_first():
    r = Registry(SIZE)
    r.record_task("11111", [1, 2, 3], [7])
    r.record_task("00000", [1, 2, 3], [9])
    r.record_task("00000", [1, 2, 3], [9])
    assert list(r.ordered_indices("11111")[:3]) == [7, 9, 0]
    assert list(r.ordered_indices("00000")[:3]) == [9, 7, 0]


def test_order_is_a_permutation():
    r = Registry(SIZE)
    r.record_task("a", range(10), [4, 5])
    order = r.ordered_indices("a")
    assert sorted(order) == list(range(SIZE))


def test_dormancy_postpones_then_a_hit_reactivates(monkeypatch):
    monkeypatch.setattr(reg, "DORMANCY_TASKS", 3)
    r = Registry(SIZE)
    for _ in range(3):
        r.record_task("p", [0, 1], [])
    order = list(r.ordered_indices("p"))
    assert order[-2:] == [0, 1] and r.dormant_count() == 2
    r.record_task("p", [0], [0])
    assert r.dormant_count() == 1 and r.ordered_indices("p")[0] == 0
    assert any(entry["reactivated"] for entry in r.log)


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(reg, "REGISTRY_DIR", tmp_path)
    r = Registry(SIZE)
    r.record_task("p", [1, 2], [2])
    loaded = load_registry(r.save("snap"))
    assert np.array_equal(loaded.ordered_indices("p"), r.ordered_indices("p"))
    assert loaded.tasks_seen == 1


def test_failed_entries_are_postponed_not_dropped():
    r = Registry(SIZE)
    r.record_task("p", [0, 1, 2], [], failed=[1])
    order = list(r.ordered_indices("p"))
    assert order[-1] == 1 and sorted(order) == list(range(SIZE))
    assert list(r.ordered_indices("q")) == list(range(SIZE))


def test_failure_memory_is_exact_and_a_hit_outranks_it():
    r = Registry(SIZE)
    r.record_task("p", [0, 1], [], failed=[1])
    r.record_task("p", [0, 1], [1], failed=[])
    assert r.ordered_indices("p")[0] == 1
    r.record_task("p", [3], [3], failed=[3])
    assert r.fails["p"][3] == 0


def test_failure_memory_survives_save_and_load(tmp_path, monkeypatch):
    monkeypatch.setattr(reg, "REGISTRY_DIR", tmp_path)
    r = Registry(SIZE)
    r.record_task("p", [1], [], failed=[1])
    loaded = load_registry(r.save("snap"))
    assert list(loaded.ordered_indices("p")) == list(r.ordered_indices("p")) and loaded.failed_count() == 1
