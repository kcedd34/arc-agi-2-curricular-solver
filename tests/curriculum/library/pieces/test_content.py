"""Unit tests for library/pieces/content.py's draw_lines_content builder
(task 4, ADR 0068): confirms the `stop_condition` parameter is wired
through into every emitted `SegmentTo` region, in each of the 4
directions, without touching the vocabulary layer's own resolution logic
(that is covered separately by tests/curriculum/spec/test_regions.py).
"""
from src.curriculum.library.pieces.content import CONTENT_PIECES, draw_lines_content
from src.curriculum.spec import vocabulary as vocab


def test_draw_lines_content_defaults_to_same_color_isolated():
    steps = draw_lines_content("elem", "g_in", background=0)
    assert len(steps) == 4
    for step in steps:
        assert isinstance(step, vocab.Emit)
        assert isinstance(step.region, vocab.SegmentTo)
        assert step.region.stop_condition == "same_color_isolated"


def test_draw_lines_content_wires_border_stop_condition():
    steps = draw_lines_content("elem", "g_in", background=0, stop_condition="border")
    directions = {step.region.direction for step in steps}
    assert directions == {"up", "down", "left", "right"}
    for step in steps:
        assert step.region.stop_condition == "border"


def test_draw_lines_content_wires_any_obstacle_stop_condition():
    steps = draw_lines_content("elem", "g_in", background=0, stop_condition="any_obstacle")
    for step in steps:
        assert step.region.stop_condition == "any_obstacle"


def test_content_pieces_registry_lists_stop_condition_param_for_draw_lines():
    piece = CONTENT_PIECES["draw_lines"]
    assert set(piece.params) == {"background", "stop_condition"}
