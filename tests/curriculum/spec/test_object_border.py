"""Unit tests for the `objeto_contorno` vocabulary additions (ADR 0081):
`RecolorObjectPart` transform op, `HasInterior` predicate and the shared
border/interior helper. Synthetic regions only, no task data.
"""
import pytest

from src.curriculum.spec import interpreter, vocabulary as vocab
from src.curriculum.spec._expressions import InterpreterError
from src.curriculum.spec._object_border import has_interior, interior_positions
from src.curriculum.spec._region_value import RegionValue

_SOLID_3X3 = [[5, 5, 5], [5, 5, 5], [5, 5, 5]]
_RING_3X3 = [[5, 5, 5], [5, None, 5], [5, 5, 5]]
_LINE_1X4 = [[5, 5, 5, 5]]


def _region(cells):
    return RegionValue(row0=2, col0=3, rows=len(cells), cols=len(cells[0]), cells=cells)


def test_solid_block_has_a_single_interior_cell():
    assert interior_positions(_SOLID_3X3) == {(1, 1)}


def test_ring_and_line_have_no_interior():
    assert not has_interior(_RING_3X3)
    assert not has_interior(_LINE_1X4)


def test_cell_next_to_a_hole_is_border_not_interior():
    cells = [[5] * 5 for _ in range(5)]
    cells[2][2] = None
    assert interior_positions(cells) == {(1, 1), (1, 3), (3, 1), (3, 3)}


def test_recolor_border_leaves_interior_and_none_untouched():
    result = interpreter._apply_transform(
        _region([[5, 5, 5], [5, 5, 5], [5, 5, 5]]), vocab.RecolorObjectPart(part="border", color=7)
    )
    assert result.cells == [[7, 7, 7], [7, 5, 7], [7, 7, 7]]
    assert (result.row0, result.col0) == (2, 3)


def test_recolor_interior_leaves_border_and_none_untouched():
    cells = [[5, 5, 5], [5, 5, 5], [5, 5, None]]
    result = interpreter._apply_transform(_region(cells), vocab.RecolorObjectPart(part="interior", color=7))
    assert result.cells == [[5, 5, 5], [5, 7, 5], [5, 5, None]]
    result = interpreter._apply_transform(_region(_SOLID_3X3), vocab.RecolorObjectPart(part="interior", color=7))
    assert result.cells == [[5, 5, 5], [5, 7, 5], [5, 5, 5]]


def test_recolor_part_rejects_unknown_part():
    with pytest.raises(InterpreterError):
        interpreter._apply_transform(_region(_SOLID_3X3), vocab.RecolorObjectPart(part="corner", color=1))


def test_has_interior_predicate_evaluates_on_a_bound_region():
    env = interpreter.Environment(bound={"input": [[0]]})
    env.bound["obj"] = _region(_SOLID_3X3)
    pred = vocab.HasInterior(region=vocab.RegionRef("obj"))
    assert interpreter.eval_predicate(pred, env) is True
    env.bound["obj"] = _region(_RING_3X3)
    assert interpreter.eval_predicate(pred, env) is False
