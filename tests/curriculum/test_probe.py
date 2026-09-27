"""Tests for probe.py against real 007bbfb7 data.

007bbfb7 is pinned to the curricular pool (docs/curriculum/partition.json),
not the probe pool, but reusing it here only exercises the checkpoint
mechanics, not any actual probe-pool selection, so it is safe.
"""
from pathlib import Path

from src.curriculum.probe import ProbeTaskResult, _checkpoint_from_task_results, load_probe_pool, run_probe_checkpoint
import src.curriculum.search.compose as compose_mod

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")
PARTITION_PATH = Path("docs/curriculum/partition.json")


def test_load_probe_pool_reads_the_real_partition_file():
    pool = load_probe_pool(PARTITION_PATH)

    assert len(pool) == 200
    assert "007bbfb7" not in pool  # pinned to the curricular pool, RN-CUR-05


def test_run_probe_checkpoint_scores_a_solved_exact_match_task():
    checkpoint = run_probe_checkpoint(["007bbfb7"], date="2026-09-21", training_dir=TRAINING_DIR)

    assert checkpoint.date == "2026-09-21"
    assert checkpoint.num_tasks == 1
    assert checkpoint.num_unanimous == 1
    assert checkpoint.num_solved == 1
    assert checkpoint.accuracy == 1.0


def test_run_probe_checkpoint_handles_empty_pool_without_division_error():
    checkpoint = run_probe_checkpoint([], date="2026-09-21", training_dir=TRAINING_DIR)

    assert checkpoint.num_tasks == 0
    assert checkpoint.accuracy == 0.0


def test_run_probe_checkpoint_sequential_and_parallel_agree_on_real_tasks():
    sample = ["007bbfb7", "00576224", "009d5c81", "00d62c1b", "00dbd492"]

    sequential = run_probe_checkpoint(sample, date="2026-09-22", training_dir=TRAINING_DIR, max_workers=1)
    parallel = run_probe_checkpoint(sample, date="2026-09-22", training_dir=TRAINING_DIR, max_workers=4)

    assert sequential == parallel


def test_run_probe_checkpoint_scores_zero_when_nothing_solves():
    original_layouts = compose_mod.LAYOUT_PIECES
    try:
        compose_mod.LAYOUT_PIECES = {}  # empty: nothing solves anymore
        checkpoint = run_probe_checkpoint(["007bbfb7"], date="2026-09-21", training_dir=TRAINING_DIR)
        assert checkpoint.num_tasks == 1
        assert checkpoint.num_unanimous == 0
        assert checkpoint.num_solved == 0
        assert checkpoint.accuracy == 0.0
    finally:
        compose_mod.LAYOUT_PIECES = original_layouts


def test_checkpoint_counts_sequence_budget_and_deadline_cuts():
    results = [
        ProbeTaskResult("a", unanimous=False, solved=False, budget_hit=True),
        ProbeTaskResult("b", unanimous=False, solved=False, budget_hit=True, deadline_hit=True),
        ProbeTaskResult("c", unanimous=True, solved=True, solved_at_1=True),
    ]
    checkpoint = _checkpoint_from_task_results(["a", "b", "c"], "2026-09-24", results)
    assert (checkpoint.num_budget_hit, checkpoint.num_deadline_hit) == (2, 1)
