"""Unit tests for the object pack's vocabulary-v2 transform ops (Section
3.3): recolor(region, color), erase(region, background),
fill_bbox(region, color), translate(region, dr, dc).
"""
import pytest

from src.curriculum.spec import interpreter, vocabulary as vocab
from src.curriculum.spec._expressions import InterpreterError
from src.curriculum.spec._region_value import RegionValue


def _region(row0, col0, cells):
    rows = len(cells)
    cols = len(cells[0]) if rows else 0
    return RegionValue(row0=row0, col0=col0, rows=rows, cols=cols, cells=cells)


def test_recolor_object_repaints_only_member_cells():
    region = _region(0, 0, [[5, None], [5, 5]])
    result = interpreter._apply_transform(region, vocab.RecolorObject(color=7))
    assert result.cells == [[7, None], [7, 7]]
    assert (result.row0, result.col0) == (0, 0)


def test_erase_repaints_member_cells_to_background():
    region = _region(1, 2, [[5, None], [5, 5]])
    result = interpreter._apply_transform(region, vocab.Erase(background=0))
    assert result.cells == [[0, None], [0, 0]]
    assert (result.row0, result.col0) == (1, 2)


def test_fill_bbox_repaints_every_cell_including_none_holes():
    region = _region(0, 0, [[5, None], [5, 5]])
    result = interpreter._apply_transform(region, vocab.FillBbox(color=9))
    assert result.cells == [[9, 9], [9, 9]]


def test_translate_shifts_position_without_changing_cells():
    region = _region(2, 3, [[5, None], [5, 5]])
    result = interpreter._apply_transform(region, vocab.Translate(dr=1, dc=-2))
    assert (result.row0, result.col0) == (3, 1)
    assert result.cells == [[5, None], [5, 5]]


def test_emit_skips_none_source_cells_preserving_seeded_canvas():
    env = interpreter.Environment(bound={"input": [[0]]})
    env.output_grid = [[1, 2], [3, 4]]
    region = vocab.RegionRef("obj")
    env.bound["obj"] = _region(0, 0, [[9, None], [None, 9]])
    step = vocab.Emit(region=region, source=vocab.Copy(source=vocab.Ref("obj")))
    interpreter._exec_emit(step, env)
    assert env.output_grid == [[9, 2], [3, 9]]


def test_emit_out_of_bounds_raises_interpreter_error():
    env = interpreter.Environment(bound={"input": [[0]]})
    env.output_grid = [[1]]
    env.bound["obj"] = _region(5, 5, [[9]])
    step = vocab.Emit(region=vocab.RegionRef("obj"), source=vocab.Copy(source=vocab.Ref("obj")))
    with pytest.raises(InterpreterError):
        interpreter._exec_emit(step, env)
