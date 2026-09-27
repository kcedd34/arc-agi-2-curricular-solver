"""`gen:<expr>` measures reached through `measure_value` (ADR 0110)."""
import pytest

from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._gen_atoms import BOOL, INT
from src.curriculum.spec._gen_expr import parse
from src.curriculum.spec._measures import measure_value
from src.curriculum.spec._region_value import RegionValue
from src.curriculum.spec.interpreter import _partition_grid
from src.curriculum.spec import vocabulary as vocab

GRID = [
    [0, 0, 0, 0, 0, 0],
    [0, 3, 3, 0, 5, 0],
    [0, 3, 0, 0, 5, 0],
    [0, 0, 0, 0, 0, 0],
    [7, 0, 0, 0, 0, 2],
]


def _objects():
    return _partition_grid(GRID, vocab.Objects(4, 0, True))


@pytest.mark.parametrize("atom", ["size", "width", "height", "gap", "colors", "hole_cells"])
def test_own_atoms_equal_existing_measures(atom):
    for region in _objects():
        assert measure_value(region, "gen:" + atom) == measure_value(region, atom)


def test_group_ops_broadcast_over_the_partition():
    regions = _objects()
    sizes = [measure_value(r, "gen:size") for r in regions]
    assert [measure_value(r, "gen:gmax(size)") for r in regions] == [max(sizes)] * len(regions)
    assert [measure_value(r, "gen:gsum(size)") for r in regions] == [sum(sizes)] * len(regions)
    assert [measure_value(r, "gen:eq(size,gmax(size))") for r in regions] == [int(s == max(sizes)) for s in sizes]


def test_rank_counts_distinct_smaller_values():
    regions = _objects()
    sizes = [measure_value(r, "gen:size") for r in regions]
    for region, size in zip(regions, sizes):
        assert measure_value(region, "gen:rank(size)") == len({s for s in sizes if s < size})


def test_sibling_atoms_need_a_partition_context():
    region = _objects()[0]
    assert measure_value(region, "gen:min_dist") >= 0
    bare = RegionValue(region.row0, region.col0, region.rows, region.cols, region.cells)
    with pytest.raises(InterpreterError):
        measure_value(bare, "gen:min_dist")


def test_types_are_checked():
    assert parse("size").type == INT
    assert parse("lt(size,gmax(size))").type == BOOL
    with pytest.raises(InterpreterError):
        parse("add(color,size)")
    with pytest.raises(InterpreterError):
        parse("nosuchatom")


def test_group_mode_tie_is_invalid():
    regions = _partition_grid([[1, 0, 2, 0, 0]], vocab.Objects(4, 0, True))
    with pytest.raises(InterpreterError):
        measure_value(regions[0], "gen:gmode(color)")
