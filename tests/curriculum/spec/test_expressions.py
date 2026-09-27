"""Unit tests for _expressions.py's IsIsolated predicate (ADR 0066) and
the object pack's vocabulary-v2 predicates (Section 3.3): size_eq,
color_eq, has_unique_color, and the tie-safe, true-size fix to the
pre-existing (previously untested) is_largest/is_smallest/size_gt.

Split from test_interpreter.py since these exercise `is_isolated_cell`
and `eval_predicate` directly rather than a full step sequence.
"""
import pytest

from src.curriculum.spec import vocabulary as vocab
from src.curriculum.spec._expressions import (
    InterpreterError,
    eval_predicate,
    is_isolated_cell,
)
from src.curriculum.spec._region_value import RegionValue


class _FakeEnv:
    def __init__(self, bound):
        self.bound = bound
        self.output_grid = None
        self.active_extents = []


def _region(row0, col0, cells):
    rows = len(cells)
    cols = len(cells[0]) if rows else 0
    return RegionValue(row0=row0, col0=col0, rows=rows, cols=cols, cells=cells)


def test_is_isolated_cell_true_for_lone_non_background_cell():
    grid = [
        [0, 0, 0],
        [0, 5, 0],
        [0, 0, 0],
    ]
    assert is_isolated_cell(grid, 1, 1, background=0) is True


def test_is_isolated_cell_false_for_background_cell():
    grid = [[0, 0], [0, 0]]
    assert is_isolated_cell(grid, 0, 0, background=0) is False


def test_is_isolated_cell_false_when_same_color_neighbor_exists():
    grid = [
        [0, 0, 0],
        [0, 5, 5],
        [0, 0, 0],
    ]
    assert is_isolated_cell(grid, 1, 1, background=0) is False


def test_is_isolated_cell_true_when_neighbor_is_different_color():
    grid = [
        [0, 0, 0],
        [0, 5, 3],
        [0, 0, 0],
    ]
    assert is_isolated_cell(grid, 1, 1, background=0) is True


def test_is_isolated_cell_out_of_bounds_raises_interpreter_error():
    grid = [[0, 0], [0, 0]]
    with pytest.raises(InterpreterError):
        is_isolated_cell(grid, 5, 5, background=0)


# --- size_gt/size_eq: true object-cell count, not bounding-box area --------


def test_size_gt_uses_true_object_size_not_bbox_area():
    """An L-shaped object (3 cells) has a 2x2=4-cell bbox; size_gt(2) must
    be true (3 > 2) and size_gt(3) false, neither driven by the 4-cell
    bbox area (the pre-existing, previously-untested bug this fixes)."""
    l_shape = _region(0, 0, [[5, None], [5, 5]])
    env = _FakeEnv({"r": l_shape})
    assert eval_predicate(vocab.SizeGt(region=vocab.RegionRef("r"), n=2), env) is True
    assert eval_predicate(vocab.SizeGt(region=vocab.RegionRef("r"), n=3), env) is False


def test_size_eq_uses_true_object_size():
    l_shape = _region(0, 0, [[5, None], [5, 5]])
    env = _FakeEnv({"r": l_shape})
    assert eval_predicate(vocab.SizeEq(region=vocab.RegionRef("r"), n=3), env) is True
    assert eval_predicate(vocab.SizeEq(region=vocab.RegionRef("r"), n=4), env) is False


# --- is_largest/is_smallest: true size, never a silent tie-break -----------


def test_is_largest_picks_the_unique_largest_by_true_size():
    small = _region(0, 0, [[5]])
    large = _region(0, 1, [[5, 5], [5, None]])  # true size 3, bbox area 4
    env = _FakeEnv({"items": [small, large], "target": large})
    pred = vocab.IsLargest(region=vocab.RegionRef("target"), list_ref=vocab.Ref("items"))
    assert eval_predicate(pred, env) is True
    env2 = _FakeEnv({"items": [small, large], "target": small})
    pred2 = vocab.IsLargest(region=vocab.RegionRef("target"), list_ref=vocab.Ref("items"))
    assert eval_predicate(pred2, env2) is False


def test_is_largest_false_for_every_item_on_a_true_tie():
    a = _region(0, 0, [[5]])
    b = _region(0, 1, [[5]])
    env = _FakeEnv({"items": [a, b], "target": a})
    pred = vocab.IsLargest(region=vocab.RegionRef("target"), list_ref=vocab.Ref("items"))
    assert eval_predicate(pred, env) is False


def test_is_smallest_picks_the_unique_smallest_by_true_size():
    small = _region(0, 0, [[5]])
    large = _region(0, 1, [[5, 5]])
    env = _FakeEnv({"items": [small, large], "target": small})
    pred = vocab.IsSmallest(region=vocab.RegionRef("target"), list_ref=vocab.Ref("items"))
    assert eval_predicate(pred, env) is True


def test_is_smallest_false_for_every_item_on_a_true_tie():
    a = _region(0, 0, [[5]])
    b = _region(0, 1, [[5]])
    env = _FakeEnv({"items": [a, b], "target": b})
    pred = vocab.IsSmallest(region=vocab.RegionRef("target"), list_ref=vocab.Ref("items"))
    assert eval_predicate(pred, env) is False


# --- color_eq/has_unique_color: strict single-color object semantics ------


def test_object_color_eq_true_for_matching_monochromatic_object():
    region = _region(0, 0, [[5, None], [5, 5]])
    env = _FakeEnv({"r": region})
    pred = vocab.ObjectColorEq(region=vocab.RegionRef("r"), color=5)
    assert eval_predicate(pred, env) is True


def test_object_color_eq_false_for_multicolor_object_never_a_majority_guess():
    region = _region(0, 0, [[5, 3], [5, 5]])
    env = _FakeEnv({"r": region})
    pred = vocab.ObjectColorEq(region=vocab.RegionRef("r"), color=5)
    assert eval_predicate(pred, env) is False


def test_has_unique_color_true_when_no_other_object_shares_the_color():
    red = _region(0, 0, [[5]])
    blue = _region(0, 1, [[3]])
    env = _FakeEnv({"items": [red, blue], "target": red})
    pred = vocab.HasUniqueColor(region=vocab.RegionRef("target"), list_ref=vocab.Ref("items"))
    assert eval_predicate(pred, env) is True


def test_has_unique_color_false_when_another_object_shares_the_color():
    red_a = _region(0, 0, [[5]])
    red_b = _region(0, 1, [[5]])
    env = _FakeEnv({"items": [red_a, red_b], "target": red_a})
    pred = vocab.HasUniqueColor(region=vocab.RegionRef("target"), list_ref=vocab.Ref("items"))
    assert eval_predicate(pred, env) is False


def test_has_unique_color_false_for_multicolor_object():
    multicolor = _region(0, 0, [[5, 3]])
    other = _region(0, 1, [[7]])
    env = _FakeEnv({"items": [multicolor, other], "target": multicolor})
    pred = vocab.HasUniqueColor(region=vocab.RegionRef("target"), list_ref=vocab.Ref("items"))
    assert eval_predicate(pred, env) is False
