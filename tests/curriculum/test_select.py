"""Tests for select.py: curricular-pool loading and next-task selection."""
from pathlib import Path

from src.curriculum.select import DEFAULT_PARTITION_PATH, load_curricular_pool, select_next_task
from src.curriculum.state import CurriculumState, PartitionRef


def _state_with_solved(solved_tasks):
    return CurriculumState(
        schema_version=1,
        updated_at="2026-09-21",
        current_stage="stage_0",
        stage_status="in_progress",
        partition_ref=PartitionRef(
            path="docs/curriculum/partition.json",
            seed=20260921,
            total_training_tasks=1000,
            curricular_pool_size=800,
            probe_pool_size=200,
            pinned_curricular_task_ids=["007bbfb7"],
        ),
        remaining_stage_0_items=[],
        blocked_on=[],
        solved_tasks=solved_tasks,
        next_task="",
        probe_pool_checkpoints=[],
        library_version="v0",
        next_step=1,
    )


def test_load_curricular_pool_from_real_partition_file():
    pool = load_curricular_pool(DEFAULT_PARTITION_PATH)
    assert isinstance(pool, list)
    assert "007bbfb7" in pool
    assert len(pool) == 800


def test_select_next_task_skips_solved_tasks():
    pool = ["a", "b", "c"]
    state = _state_with_solved(["a"])

    assert select_next_task(state, pool) == "b"


def test_select_next_task_returns_first_when_none_solved():
    pool = ["a", "b", "c"]
    state = _state_with_solved([])

    assert select_next_task(state, pool) == "a"


def test_select_next_task_returns_none_when_all_solved():
    pool = ["a", "b"]
    state = _state_with_solved(["a", "b"])

    assert select_next_task(state, pool) is None
