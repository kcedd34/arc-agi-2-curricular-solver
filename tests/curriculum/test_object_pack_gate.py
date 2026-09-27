"""Unit tests for the Phase 7 curricular gate driver (object-pack.md
Section 5.5, RN-CUR-36 condition 2): pool filtering and report
formatting, without touching real task files or state.json."""
import dataclasses
from pathlib import Path

from src.curriculum.object_pack_gate import (
    GateTaskResult,
    budget_cut_counts,
    format_gate_report,
    not_yet_accepted_pool,
    resolved_task_ids,
    run_gate_check,
)
from src.curriculum.state import CurriculumState, PartitionRef

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")
SAMPLE_TASK_IDS = ["007bbfb7", "00576224", "009d5c81", "00d62c1b", "00dbd492"]


def _state(solved_tasks):
    return CurriculumState(
        schema_version=1,
        updated_at="2026-09-22",
        current_stage="stage_1",
        stage_status="complete",
        partition_ref=PartitionRef(
            path="docs/curriculum/partition.json",
            seed=1,
            total_training_tasks=1000,
            curricular_pool_size=800,
            probe_pool_size=200,
            pinned_curricular_task_ids=[],
        ),
        remaining_stage_0_items=[],
        blocked_on=[],
        solved_tasks=solved_tasks,
        next_task="x",
        probe_pool_checkpoints=[],
        library_version="v4",
        next_step=7,
    )


def test_not_yet_accepted_pool_excludes_solved_tasks():
    state = _state(["a", "c"])
    assert not_yet_accepted_pool(state, ["a", "b", "c", "d"]) == ["b", "d"]


def test_resolved_task_ids_filters_solved_field_only():
    results = [
        GateTaskResult("a", unanimous=True, solved=True, object_verified_count=1, main_verified_count=0),
        GateTaskResult("b", unanimous=False, solved=False, object_verified_count=0, main_verified_count=0),
        GateTaskResult("c", unanimous=False, solved=False, object_verified_count=2, main_verified_count=1),
        GateTaskResult("d", unanimous=True, solved=True, object_verified_count=0, main_verified_count=3),
    ]
    assert resolved_task_ids(results) == ["a", "d"]


def test_resolved_task_ids_excludes_unanimous_but_wrong():
    """The exact regression this correction guards: candidates agree with
    each other (unanimous) but not with the gabarito (not solved) must
    never be treated as accepted."""
    results = [GateTaskResult("a", unanimous=True, solved=False, object_verified_count=1, main_verified_count=0)]
    assert resolved_task_ids(results) == []


def test_format_gate_report_lists_resolved_ids_and_per_task_detail():
    results = [
        GateTaskResult("a", unanimous=True, solved=True, object_verified_count=1, main_verified_count=0,
                        solved_at_1=True),
        GateTaskResult("b", unanimous=False, solved=False, object_verified_count=0, main_verified_count=0),
        GateTaskResult("c", unanimous=False, solved=True, object_verified_count=2, main_verified_count=0),
    ]
    report = format_gate_report(results)
    assert "two-attempt): solved=2 (@1=1, @2=1)" in report
    assert "Solved only by attempt 2: ['c']" in report
    assert "  - a" in report
    assert "a: unanimous=True solved=True at1=True object_verified=1 main_verified=0" in report
    assert "b: unanimous=False solved=False at1=False object_verified=0 main_verified=0" in report


def test_run_gate_check_sequential_and_parallel_agree_on_real_tasks():
    sequential = run_gate_check(SAMPLE_TASK_IDS, training_dir=TRAINING_DIR, max_workers=1)
    parallel = run_gate_check(SAMPLE_TASK_IDS, training_dir=TRAINING_DIR, max_workers=4)

    assert sequential == parallel
    assert [r.task_id for r in sequential] == SAMPLE_TASK_IDS
    assert all(r.error is None for r in sequential)


def test_gate_report_counts_budget_and_deadline_cuts_per_task():
    results = [
        GateTaskResult("a", unanimous=False, solved=False, object_verified_count=0, main_verified_count=0, budget_hit=True),
        GateTaskResult("b", unanimous=False, solved=False, object_verified_count=0, main_verified_count=0, budget_hit=True,
                        deadline_hit=True),
        GateTaskResult("c", unanimous=True, solved=True, object_verified_count=1, main_verified_count=0),
    ]
    assert budget_cut_counts(results) == (2, 1)
    report = format_gate_report(results)
    assert "Sequence budget cuts: budget_hit=2 deadline_hit=1 of 3" in report
    assert "budget_hit tasks: ['a', 'b']" in report
    assert "deadline_hit tasks: ['b']" in report
    assert "a: unanimous=False solved=False at1=False object_verified=0 main_verified=0 budget_hit=True" in report
