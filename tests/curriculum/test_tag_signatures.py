"""Train-pair rule-family signatures (ADR 0085)."""
from src.curriculum import tag_signatures as sig


def _pair(a, b):
    return {"input": a, "output": b}


def _empty(n=5):
    return [[0] * n for _ in range(n)]


def _with(grid, cells):
    out = [row[:] for row in grid]
    for (r, c), v in cells.items():
        out[r][c] = v
    return out


def test_halo_family_adds_only_cells_adjacent_to_foreground():
    a = _with(_empty(), {(2, 2): 5})
    b = _with(a, {(1, 2): 1, (3, 2): 1, (2, 1): 1, (2, 3): 1})
    assert sig.rule_family([_pair(a, b)]) == "halo"


def test_connect_family_fills_between_same_colored_cells():
    a = _with(_empty(), {(2, 0): 3, (2, 4): 3})
    b = _with(a, {(2, 1): 3, (2, 2): 3, (2, 3): 3})
    assert sig.rule_family([_pair(a, b)]) == "connect"


def test_marker_line_family_is_a_ray_not_a_halo_nor_a_connection():
    a = _with(_empty(), {(2, 0): 3})
    b = _with(a, {(2, 1): 3, (2, 2): 3, (2, 3): 3, (2, 4): 3})
    assert sig.rule_family([_pair(a, b)]) == "marker_line"


def test_translation_family_needs_one_nonzero_offset():
    a = _with(_empty(), {(1, 1): 4})
    b = _with(_empty(), {(1, 2): 4})
    assert sig.rule_family([_pair(a, b)]) == "translation"


def test_in_place_recolor_is_not_a_translation():
    a = _with(_empty(), {(1, 1): 4})
    b = _with(_empty(), {(1, 1): 6})
    assert not sig.is_translation_family([_pair(a, b)])


def test_frequency_extreme_requires_a_unique_extreme_color():
    a = _with(_empty(), {(0, 0): 1, (0, 1): 1, (0, 2): 1, (4, 4): 2, (4, 3): 2, (2, 2): 7})
    b = _with(a, {(1, 1): 1})
    assert sig.paints_frequency_extreme([_pair(a, b)]) == "most"


def test_no_family_when_shapes_differ():
    assert sig.rule_family([_pair(_empty(5), _empty(3))]) is None
    assert sig.output_shape_kind([_pair(_empty(5), _empty(3))]) == "smaller"


def test_diff_kind_separates_add_remove_recolor_and_mixed():
    a = _with(_empty(), {(1, 1): 4})
    assert sig.diff_kind([_pair(a, _empty())]) == "remove"
    assert sig.diff_kind([_pair(a, _with(_empty(), {(1, 1): 6}))]) == "recolor"
    assert sig.diff_kind([_pair(a, _with(a, {(0, 0): 4}))]) == "add"
