"""Tests for validation.py: schema checks and the real regression re-run."""
from src.curriculum.state import CurriculumState, PartitionRef
from src.curriculum.validation import validate_state, validate_state_schema


def _valid_state(**overrides):
    defaults = dict(
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
        solved_tasks=[],
        next_task="007bbfb7",
        probe_pool_checkpoints=[],
        library_version="v0",
        next_step=1,
    )
    defaults.update(overrides)
    return CurriculumState(**defaults)


def test_validate_state_schema_accepts_a_valid_state():
    assert validate_state_schema(_valid_state()) == []


def test_validate_state_schema_flags_unexpected_schema_version():
    errors = validate_state_schema(_valid_state(schema_version=2))
    assert any("schema_version" in e for e in errors)


def test_validate_state_schema_flags_unexpected_current_stage():
    errors = validate_state_schema(_valid_state(current_stage="stage_99"))
    assert any("current_stage" in e for e in errors)


def test_validate_state_schema_flags_unexpected_stage_status():
    errors = validate_state_schema(_valid_state(stage_status="done"))
    assert any("stage_status" in e for e in errors)


def test_validate_state_schema_flags_next_task_already_solved():
    errors = validate_state_schema(_valid_state(next_task="007bbfb7", solved_tasks=["007bbfb7"]))
    assert any("next_task" in e for e in errors)


def test_validate_state_end_to_end_with_no_solved_tasks_is_valid():
    result = validate_state(_valid_state())

    assert result.schema_errors == []
    assert result.regression.checked == []
    assert result.regression.regressed == []
    assert result.is_valid is True


def test_validate_state_end_to_end_reruns_regression_for_solved_tasks():
    result = validate_state(_valid_state(solved_tasks=["007bbfb7"], next_task=""))

    assert result.regression.checked == ["007bbfb7"]
    assert result.regression.regressed == []
    assert result.is_valid is True
