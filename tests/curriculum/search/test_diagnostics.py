"""Tests for search/diagnostics.py's search-log instrumentation on real 007bbfb7 data."""
from pathlib import Path

from src.curriculum.loader import load_task
from src.curriculum.search.diagnostics import build_search_log

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def test_build_search_log_solves_007bbfb7_with_full_classification():
    task = load_task(TRAINING_DIR / "007bbfb7.json")
    log = build_search_log(task)

    assert log.final_status == "solved"
    assert log.total_enumerated > 0
    # >= 1, not == 1: general content pieces added for later tasks (e.g.
    # draw_lines/keep, ADR 0066) legitimately enumerate extra candidates
    # against every task, since the library is shared (RN-CUR-33).
    assert log.verified_count >= 1
    assert log.discarded_count == log.total_enumerated - log.verified_count

    assert any(
        c.classification == "verified"
        and c.composition.layout_name == "block_grid"
        and c.composition.layout_params == {"scale_rows": 3, "scale_cols": 3}
        and c.composition.selector_name == "input_cell_not_background"
        and c.composition.selector_params == {"background": 0}
        and c.composition.selected_content_name == "copy"
        and c.composition.not_selected_content_name == "fill"
        for c in log.candidates
    )

    family_key = "block_grid+input_cell_not_background+copy+fill"
    counts = log.by_family[family_key]
    assert counts["verified"] == 1
    assert sum(counts.values()) == counts["verified"] + counts["discarded_train_mismatch"] + counts[
        "discarded_interpreter_error"
    ]


def test_build_search_log_no_candidate_when_layout_pieces_empty():
    import src.curriculum.search.compose as compose_mod

    task = load_task(TRAINING_DIR / "007bbfb7.json")
    original_layouts = compose_mod.LAYOUT_PIECES
    try:
        compose_mod.LAYOUT_PIECES = {}
        log = build_search_log(task)
        assert log.final_status == "no_candidate"
        assert log.total_enumerated == 0
        assert log.verified_count == 0
    finally:
        compose_mod.LAYOUT_PIECES = original_layouts
