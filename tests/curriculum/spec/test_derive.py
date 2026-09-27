"""Derived-parameter layer (ADR 0107): new properties, derivation operators
and the table lookup, on synthetic grids with no task dependency."""
import pytest

from src.curriculum.perception.objects import segment_objects
from src.curriculum.spec import _derive, interpreter, vocabulary as vocab
from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._measures import MEASURE_NAMES, measure_value
from src.curriculum.spec._region_value import RegionValue


def region(cells, row0=0, col0=0):
    return RegionValue(row0=row0, col0=col0, rows=len(cells), cols=len(cells[0]), cells=cells)


def test_registry_lists_the_new_properties():
    for name in ("row_parity", "col_parity", "dominant_color"):
        assert name in MEASURE_NAMES


def test_parity_follows_the_position():
    assert measure_value(region([[1]], row0=3, col0=4), "row_parity") == 1
    assert measure_value(region([[1]], row0=3, col0=4), "col_parity") == 0


def test_dominant_color_and_tie():
    assert measure_value(region([[1, 1, 2]]), "dominant_color") == 1
    with pytest.raises(InterpreterError):
        measure_value(region([[1, 2]]), "dominant_color")


def items():
    return [region([[1, 1]]), region([[2]]), region([[3, 3, 3]])]


def test_region_operators():
    assert _derive.derive_from_regions(items(), "min", "size") == 1
    assert _derive.derive_from_regions(items(), "max", "size") == 3
    assert _derive.derive_from_regions(items(), "total", "size") == 6


def test_unique_needs_exactly_one_value():
    with pytest.raises(InterpreterError):
        _derive.derive_from_regions(items(), "unique", "size")
    assert _derive.derive_from_regions([region([[1]]), region([[1]]), region([[2, 2]])], "unique", "size") == 2


def test_mode_rejects_a_tie_and_empty_list():
    assert _derive.derive_from_regions([region([[1]]), region([[2]]), region([[3, 3]])], "mode", "size") == 1
    with pytest.raises(InterpreterError):
        _derive.derive_from_regions(items(), "mode", "size")
    with pytest.raises(InterpreterError):
        _derive.derive_from_regions([], "min", "size")


def test_grid_colour_resources():
    grid = [[0, 1, 1], [2, 1, 3], [3, 3, 3]]
    assert _derive.derive_from_grid(grid, "rarest_color", 0) == 2
    assert _derive.derive_from_grid(grid, "common_color", 0) == 3
    with pytest.raises(InterpreterError):
        _derive.derive_from_grid([[0, 1, 2]], "rarest_color", 0)
    with pytest.raises(InterpreterError):
        _derive.derive_from_grid([[0, 0]], "common_color", 0)


def test_table_lookup_is_never_invented():
    table = (((1,), 5), ((2,), 6))
    assert _derive.table_lookup(table, (2,)) == 6
    with pytest.raises(InterpreterError):
        _derive.table_lookup(table, (9,))


def test_interpreter_evaluates_derive_and_table_lookup():
    grid = [[0, 1, 1], [0, 0, 0], [2, 0, 0]]
    out = interpreter.run(_expr_program(vocab.Derive(vocab.Ref("g"), "rarest_color", background=0)), grid)[0]
    assert out == [[2] * 3] * 3
    lookup = vocab.TableLookup(keys=(vocab.Derive(vocab.Ref("g"), "common_color", background=0),), table=(((1,), 7),))
    assert interpreter.run(_expr_program(lookup), grid)[0] == [[7] * 3] * 3


def _expr_program(expr):
    return [
        vocab.Bind("g", vocab.Ref("input")),
        vocab.Bind("v", expr),
        vocab.ShapeOut(vocab.Attr(vocab.Ref("g"), "rows"), vocab.Attr(vocab.Ref("g"), "cols")),
        vocab.Seed(vocab.Ref("g")),
        vocab.Emit(region=vocab.WholeGrid(vocab.Ref("g")), source=vocab.Fill(color=vocab.Ref("v"))),
        vocab.Compose(default_color=0),
    ]


def _paint_program(op):
    return [
        vocab.Bind("g", vocab.Ref("input")),
        vocab.ShapeOut(vocab.Attr(vocab.Ref("g"), "rows"), vocab.Attr(vocab.Ref("g"), "cols")),
        vocab.Seed(vocab.Ref("g")),
        vocab.Partition(vocab.Ref("g"), vocab.Objects(background=0, connectivity=4, single_color=True), "objs"),
        vocab.ForEach(
            vocab.Ref("objs"),
            [vocab.Transform(vocab.RegionRef("o"), op, result_name="t"),
             vocab.Emit(region=vocab.RegionRef("t"), source=vocab.Copy(vocab.Ref("t")))],
            element_name="o",
        ),
        vocab.Compose(default_color=0),
    ]


def test_parametric_color_is_resolved_before_the_op_runs():
    rarest = vocab.Derive(vocab.Ref("g"), "rarest_color", background=0)
    grid = [[1, 1, 0, 0], [1, 1, 0, 3], [0, 0, 0, 0]]
    out = interpreter.run(_paint_program(vocab.RecolorObject(rarest)), grid)[0]
    assert out == [[3, 3, 0, 0], [3, 3, 0, 3], [0, 0, 0, 0]]


def test_literal_color_still_works():
    grid = [[1, 0], [0, 0]]
    assert interpreter.run(_paint_program(vocab.RecolorObject(4)), grid)[0] == [[4, 0], [0, 0]]


def test_parametric_shift_from_a_derived_value():
    one = vocab.BinOp("-", vocab.Derive(vocab.Ref("objs"), "max", "height"), 1)
    grid = [[1, 0], [1, 0], [0, 0]]
    out = interpreter.run(_paint_program(vocab.Translate(dr=one, dc=0)), grid)[0]
    assert out == [[1, 0], [1, 0], [1, 0]]  # the seed keeps the original, the copy lands one row down
