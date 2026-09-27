"""Tests for search/compose.py's composition enumeration, in particular
RN-CUR-33 step 3's layout/selector compatibility pruning: an
incompatible pairing (e.g. `input_cell_not_background` when the tile
scale doesn't match the input's own shape) must never be enumerated,
not merely fail verification later."""
from pathlib import Path

from src.curriculum.loader import load_task
from src.curriculum.search.compose import enumerate_compositions

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def test_00576224_never_enumerates_incompatible_selector():
    """`block_grid`'s scale for 00576224 does not match the input's own
    shape, so `input_cell_not_background` must never be paired with it
    (identity_canvas, unaffected by this pruning rule, may still pair
    with it: its Cells() partition is always in-bounds by construction,
    ADR 0066)."""
    task = load_task(TRAINING_DIR / "00576224.json")
    compositions = list(enumerate_compositions(task))
    assert compositions
    assert all(
        not (c.layout_name == "block_grid" and c.selector_name == "input_cell_not_background")
        for c in compositions
    )
    assert {c.selector_name for c in compositions if c.layout_name == "block_grid"} == {
        "row_parity"
    }


def test_007bbfb7_keeps_compatible_selector_available():
    """block_grid's own selector set stays exactly as before (ADR 0066
    only adds identity_canvas-paired selectors, never removes or gates
    block_grid's existing ones)."""
    task = load_task(TRAINING_DIR / "007bbfb7.json")
    compositions = list(enumerate_compositions(task))
    assert {c.selector_name for c in compositions if c.layout_name == "block_grid"} == {
        "input_cell_not_background",
        "row_parity",
    }


def test_isolated_point_never_paired_with_block_grid():
    """ADR 0066: `isolated_point` reads the loop element's own (row, col)
    as a real input coordinate, which only holds for `identity_canvas`'s
    Cells() partition, never for `block_grid`'s synthetic IndexGrid."""
    task = load_task(TRAINING_DIR / "007bbfb7.json")
    compositions = list(enumerate_compositions(task))
    isolated_point_layouts = {
        c.layout_name for c in compositions if c.selector_name == "isolated_point"
    }
    assert isolated_point_layouts in ({"identity_canvas"}, set())


def test_ded97339_enumerates_identity_canvas_and_isolated_point():
    task = load_task(TRAINING_DIR / "ded97339.json")
    compositions = list(enumerate_compositions(task))
    assert compositions
    assert any(
        c.layout_name == "identity_canvas" and c.selector_name == "isolated_point"
        for c in compositions
    )


def test_draw_lines_never_paired_with_block_grid():
    """Task 4 fix (ADR 0068): `draw_lines` reads the loop element's own
    (row, col) as a real input coordinate, which only holds for
    `identity_canvas`'s Cells() partition, never `block_grid`'s synthetic
    IndexGrid (same structural precondition as the `isolated_point`
    selector). This was a latent gap before task 4 exposed it as a real
    007bbfb7 regression once `stop_condition` added more candidates."""
    task = load_task(TRAINING_DIR / "007bbfb7.json")
    compositions = list(enumerate_compositions(task))
    assert compositions
    assert not any(
        c.layout_name == "block_grid"
        and (c.selected_content_name == "draw_lines" or c.not_selected_content_name == "draw_lines")
        for c in compositions
    )


def test_no_identical_selected_and_not_selected_pair():
    """Rodada 2 content x content pruning: a selector split where both
    branches emit the exact same steps is decorative (domain knowledge
    item 7) and must never be enumerated."""
    task = load_task(TRAINING_DIR / "ded97339.json")
    compositions = list(enumerate_compositions(task))
    assert compositions
    assert not any(
        c.selected_content_name == c.not_selected_content_name
        and c.selected_content_params == c.not_selected_content_params
        for c in compositions
    )


def test_draw_lines_never_paired_with_itself():
    """Rodada 2 content x content pruning: `draw_lines` on both branches
    contradicts the isolated-marker assumption its `SegmentTo` semantics
    depend on (ADR 0066/0068), and was the largest single driver of this
    term's size."""
    task = load_task(TRAINING_DIR / "ded97339.json")
    compositions = list(enumerate_compositions(task))
    assert compositions
    assert not any(
        c.selected_content_name == "draw_lines" and c.not_selected_content_name == "draw_lines"
        for c in compositions
    )
    assert any(c.selected_content_name == "draw_lines" for c in compositions)


def test_ded97339_enumerates_all_three_stop_conditions_for_draw_lines():
    task = load_task(TRAINING_DIR / "ded97339.json")
    compositions = list(enumerate_compositions(task))
    stop_conditions = {
        c.selected_content_params.get("stop_condition")
        for c in compositions
        if c.selected_content_name == "draw_lines"
    }
    assert stop_conditions == {"same_color_isolated", "border", "any_obstacle"}
