"""Tests for the search engine (features/params/compose/rank) on real 007bbfb7 data.

Proves the search path solves 007bbfb7 end to end, without hand-picking
background=0 or scale=3 anywhere in this test - the search must find both
itself via composition enumeration and train-pair verification, then
predict the real held-out test input via that verified candidate.
"""
from pathlib import Path

from src.curriculum.loader import load_task
from src.curriculum.search.rank import search_task

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def test_search_solves_007bbfb7_without_hardcoded_background():
    task = load_task(TRAINING_DIR / "007bbfb7.json")
    result = search_task(task)
    assert result.status == "solved"
    assert result.predictions is not None
    assert len(result.predictions) == len(task.test_inputs)
    assert any(
        v.layout_name == "block_grid"
        and v.layout_params == {"scale_rows": 3, "scale_cols": 3}
        and v.selector_name == "input_cell_not_background"
        and v.selector_params == {"background": 0}
        and v.selected_content_name == "copy"
        and v.not_selected_content_name == "fill"
        for v in result.verified
    )


def test_search_solves_ded97339_with_isolated_point_composition():
    """ADR 0066: the search must find the identity_canvas + isolated_point
    + draw_lines/keep composition itself, without hand-picking
    background=0 anywhere in this test."""
    task = load_task(TRAINING_DIR / "ded97339.json")
    result = search_task(task)
    assert result.status == "solved"
    assert result.predictions is not None
    assert len(result.predictions) == len(task.test_inputs)
    assert any(
        v.layout_name == "identity_canvas"
        and v.selector_name == "isolated_point"
        and v.selector_params == {"background": 0}
        and v.selected_content_name == "draw_lines"
        and v.not_selected_content_name == "keep"
        for v in result.verified
    )


def test_search_no_candidate_when_layout_pieces_empty():
    import src.curriculum.search.compose as compose_mod

    task = load_task(TRAINING_DIR / "007bbfb7.json")
    original_layouts = compose_mod.LAYOUT_PIECES
    try:
        compose_mod.LAYOUT_PIECES = {}
        result = search_task(task)
        assert result.status == "no_candidate"
        assert result.verified == []
        assert result.predictions is None
    finally:
        compose_mod.LAYOUT_PIECES = original_layouts
