"""Unit tests for the piece-usage audit driver (item 4 of the
2026-09-22 follow-up request)."""
from pathlib import Path

from src.curriculum.piece_usage_audit import (
    aggregate_enumeration_counts,
    classify_pieces,
    run_piece_usage_audit,
)

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")
SAMPLE_TASK_IDS = ["007bbfb7", "00576224", "009d5c81", "00d62c1b", "00dbd492"]


def test_run_piece_usage_audit_sequential_and_parallel_agree_on_real_tasks():
    sequential = run_piece_usage_audit(SAMPLE_TASK_IDS, training_dir=TRAINING_DIR, max_workers=1)
    parallel = run_piece_usage_audit(SAMPLE_TASK_IDS, training_dir=TRAINING_DIR, max_workers=4)

    assert sequential == parallel
    assert [r.task_id for r in sequential] == SAMPLE_TASK_IDS
    assert all(r.error is None for r in sequential)


def test_classify_pieces_reports_blocked_when_enumeration_count_is_zero():
    classification = classify_pieces({"objects_of_color": 0, "largest_object": 5})
    assert "blocked by pruning" in classification["objects_of_color"]
    assert "infer_colors_common_to_every_input" in classification["objects_of_color"]
    assert "enumerated 5 times" in classification["largest_object"]


def test_aggregate_enumeration_counts_sums_selector_and_content_counts_across_tasks():
    from src.curriculum.piece_usage_audit import PieceUsageTaskResult

    results = [
        PieceUsageTaskResult("a", {"largest_object": 2}, {"keep": 3}),
        PieceUsageTaskResult("b", {"largest_object": 1}, {"keep": 1, "erase_selected": 4}),
    ]
    totals = aggregate_enumeration_counts(results)
    assert totals == {"largest_object": 3, "keep": 4, "erase_selected": 4}
