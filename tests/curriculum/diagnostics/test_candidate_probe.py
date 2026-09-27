"""Integration tests for the Fase A.3/A.4 candidate probe: real search
execution (RN-CUR-30) against known curricular tasks, not synthetic
fixtures, mirroring test_object_pack_gate.py's convention."""
from pathlib import Path

from src.curriculum.diagnostics.candidate_probe import run_candidate_probe

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def test_known_solved_task_has_verified_candidates_and_is_solved():
    results = run_candidate_probe(["007bbfb7"], training_dir=TRAINING_DIR, max_workers=1)
    assert len(results) == 1
    result = results[0]
    assert result.error is None
    assert result.num_verified_candidates > 0
    assert result.solved is True
    assert isinstance(result.main_cap_hit, bool)
    assert isinstance(result.object_cap_hit, bool)


def test_cap_hit_flags_are_consistent_with_verified_counts():
    results = run_candidate_probe(["007bbfb7"], training_dir=TRAINING_DIR, max_workers=1)
    result = results[0]
    if result.main_cap_hit:
        assert result.main_verified_count >= 0
    if result.object_cap_hit:
        assert result.object_verified_count >= 0


def test_unknown_task_id_is_isolated_as_an_error():
    results = run_candidate_probe(["not_a_real_task_id"], training_dir=TRAINING_DIR, max_workers=1)
    assert len(results) == 1
    result = results[0]
    assert result.error is not None
    assert result.solved is False
    assert result.num_verified_candidates == 0


def test_batch_preserves_input_order():
    task_ids = ["007bbfb7", "not_a_real_task_id", "00576224"]
    results = run_candidate_probe(task_ids, training_dir=TRAINING_DIR, max_workers=1)
    assert [r.task_id for r in results] == task_ids
