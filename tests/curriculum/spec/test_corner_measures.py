"""Round 20 properties: corner_nw_color, closed, multi_cell and the
`CornerCell` region, on synthetic grids."""
from src.curriculum.spec import interpreter, vocabulary as vocab
from src.curriculum.spec._measures import GRID_ARG_MEASURES, measure_value
from src.curriculum.spec._region_value import RegionValue


def _region(row0, col0, cells):
    return RegionValue(row0=row0, col0=col0, rows=len(cells), cols=len(cells[0]), cells=cells)


def test_corner_nw_color_reads_the_diagonal_cell_outside_the_bbox():
    grid = [[0] * 5 for _ in range(5)]
    grid[1][1] = 7
    assert measure_value(_region(2, 2, [[0, 0], [0, 0]]), "corner_nw_color", grid) == 7
    assert "corner_nw_color" in GRID_ARG_MEASURES


def test_corner_nw_color_is_zero_when_the_corner_is_outside_the_grid():
    grid = [[3] * 4 for _ in range(4)]
    assert measure_value(_region(0, 1, [[0]]), "corner_nw_color", grid) == 0
    assert measure_value(_region(1, 0, [[0]]), "corner_nw_color", grid) == 0


def test_closed_is_true_for_solid_rectangles_and_regions_with_a_hole():
    solid = _region(0, 0, [[1, 1], [1, 1]])
    ring = _region(0, 0, [[1, 1, 1], [1, None, 1], [1, 1, 1]])
    cup = _region(0, 0, [[1, None, 1], [1, 1, 1]])
    assert [measure_value(r, "closed") for r in (solid, ring, cup)] == [1, 1, 0]


def test_multi_cell_separates_single_cells_from_larger_regions():
    assert measure_value(_region(0, 0, [[1]]), "multi_cell") == 0
    assert measure_value(_region(0, 0, [[1, 1]]), "multi_cell") == 1


def test_corner_cell_region_targets_one_cell_and_skips_off_grid_corners():
    def steps():
        return [
            vocab.Bind("g", vocab.Ref("input")),
            vocab.ShapeOut(vocab.Attr(vocab.Ref("g"), "rows"), vocab.Attr(vocab.Ref("g"), "cols")),
            vocab.Seed(vocab.Ref("g")),
            vocab.Partition(vocab.Ref("g"), vocab.Objects(4, 0, True), "R"),
            vocab.ForEach(
                vocab.Ref("R"),
                [vocab.Emit(region=vocab.CornerCell(vocab.RegionRef("e")), source=vocab.Fill(color=9))],
                element_name="e",
            ),
            vocab.Compose(default_color=0),
        ]

    inside = [[0, 0, 0], [0, 0, 0], [0, 0, 5]]
    assert interpreter.run(steps(), inside)[0][1][1] == 9
    corner = [[5, 0], [0, 0]]
    assert interpreter.run(steps(), corner)[0] == corner
