"""Tests for state.py's load/save round-trip and mark_task_solved, using a tmp_path."""
import dataclasses
import json
from pathlib import Path

from src.curriculum.state import CurriculumState, PartitionRef, load_state, mark_task_solved, save_state


def _sample_state() -> CurriculumState:
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
        remaining_stage_0_items=["cli.py"],
        blocked_on=[],
        solved_tasks=[],
        next_task="007bbfb7",
        probe_pool_checkpoints=[],
        library_version="v0",
        next_step=1,
    )


def test_save_then_load_round_trips(tmp_path):
    path = tmp_path / "state.json"
    state = _sample_state()

    save_state(state, path)
    loaded = load_state(path)

    assert loaded == state


def test_save_writes_indented_json_with_trailing_newline(tmp_path):
    path = tmp_path / "state.json"
    save_state(_sample_state(), path)

    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    json.loads(text)  # valid JSON


def test_load_real_project_state_file():
    state = load_state(Path("outputs/curriculum/state.json"))
    assert state.schema_version == 1
    assert "007bbfb7" in state.solved_tasks
    assert state.library_version != ""
    assert isinstance(state.next_step, int)


def test_mark_task_solved_appends_and_updates_date():
    state = _sample_state()

    updated = mark_task_solved(state, "007bbfb7", updated_at="2026-09-22")

    assert updated.solved_tasks == ["007bbfb7"]
    assert updated.updated_at == "2026-09-22"
    assert state.solved_tasks == []  # original untouched


def test_library_version_and_next_step_round_trip(tmp_path):
    path = tmp_path / "state.json"
    state = dataclasses.replace(_sample_state(), library_version="v2", next_step=6)

    save_state(state, path)
    loaded = load_state(path)

    assert loaded.library_version == "v2"
    assert loaded.next_step == 6


def test_mark_task_solved_is_idempotent():
    state = _sample_state()
    once = mark_task_solved(state, "007bbfb7", updated_at="2026-09-22")

    twice = mark_task_solved(once, "007bbfb7", updated_at="2026-09-23")

    assert twice is once
