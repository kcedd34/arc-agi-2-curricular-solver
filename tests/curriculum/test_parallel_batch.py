"""Tests for the generic process-pool batch runner (item 1 of the
2026-09-22 follow-up: parallelize batch drivers with full determinism,
default worker count, and isolated per-item failure)."""
import os

from src.curriculum.parallel_batch import default_worker_count, run_batch


def _double(item_id: str) -> int:
    return int(item_id) * 2


def _boom_on_three(item_id: str) -> int:
    if item_id == "3":
        raise ValueError("boom")
    return int(item_id) * 10


def test_default_worker_count_is_six_on_eight_cores(monkeypatch):
    monkeypatch.delenv("CURRICULUM_WORKERS", raising=False)
    monkeypatch.setattr(os, "cpu_count", lambda: 8)
    assert default_worker_count() == 6


def test_default_worker_count_never_goes_below_one(monkeypatch):
    monkeypatch.delenv("CURRICULUM_WORKERS", raising=False)
    monkeypatch.setattr(os, "cpu_count", lambda: 1)
    assert default_worker_count() == 1


def test_run_batch_sequential_and_parallel_agree(monkeypatch):
    item_ids = [str(n) for n in range(6)]

    sequential = run_batch(item_ids, _double, max_workers=1)
    parallel = run_batch(item_ids, _double, max_workers=4)

    assert sequential == parallel
    assert [item_id for item_id, _ in sequential] == item_ids


def test_run_batch_isolates_one_item_failure_sequential():
    item_ids = ["1", "2", "3", "4"]
    results = run_batch(item_ids, _boom_on_three, max_workers=1)

    outcomes = dict(results)
    assert outcomes["1"] == 10
    assert outcomes["2"] == 20
    assert isinstance(outcomes["3"], ValueError)
    assert outcomes["4"] == 40


def test_run_batch_isolates_one_item_failure_parallel():
    item_ids = ["1", "2", "3", "4"]
    results = run_batch(item_ids, _boom_on_three, max_workers=4)

    outcomes = dict(results)
    assert outcomes["1"] == 10
    assert outcomes["2"] == 20
    assert isinstance(outcomes["3"], ValueError)
    assert outcomes["4"] == 40


def test_run_batch_single_item_runs_in_process_even_with_many_workers():
    results = run_batch(["7"], _double, max_workers=4)
    assert results == [("7", 14)]
