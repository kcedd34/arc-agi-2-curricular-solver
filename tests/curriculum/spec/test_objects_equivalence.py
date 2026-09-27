"""RN-CUR-14 equivalence test (object pack Section 3.3): the trace
interpreter's own object segmentation (`interpreter._partition_objects`)
and `perception/objects.py::segment_objects` are two independently
written implementations of the same connected-component algorithm. This
test is the only place that compares them; neither module imports the
other (see test_interpreter.py::test_interpreter_independence).
"""
from typing import FrozenSet, List, Tuple

from src.curriculum.perception.objects import segment_objects
from src.curriculum.spec import interpreter
from src.curriculum.spec._region_value import RegionValue

Cell = Tuple[int, int]

GRIDS = {
    "4conn_monochrome_bg0": (
        [
            [0, 0, 0, 0, 0],
            [0, 2, 2, 0, 3],
            [0, 2, 0, 0, 3],
            [0, 0, 0, 0, 0],
        ],
        0,
    ),
    "8conn_diagonal_touch_bg0": (
        [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
        ],
        0,
    ),
    "multicolor_touching_bg0": (
        [
            [0, 1, 2, 0],
            [0, 1, 2, 0],
            [0, 0, 0, 0],
        ],
        0,
    ),
    "nonzero_background": (
        [
            [5, 5, 5, 5],
            [5, 1, 1, 5],
            [5, 5, 3, 5],
            [5, 5, 5, 5],
        ],
        5,
    ),
    "multicolor_diagonal_bg9": (
        [
            [9, 4, 9],
            [9, 9, 6],
            [9, 6, 9],
        ],
        9,
    ),
}


def _region_cells_and_colors(region: RegionValue) -> Tuple[FrozenSet[Cell], FrozenSet[int]]:
    cells = {
        (region.row0 + r, region.col0 + c)
        for r, row in enumerate(region.cells)
        for c, v in enumerate(row)
        if v is not None
    }
    colors = {v for row in region.cells for v in row if v is not None}
    return frozenset(cells), frozenset(colors)


def _region_bbox(region: RegionValue) -> Tuple[int, int, int, int]:
    return (
        region.row0,
        region.col0,
        region.row0 + region.rows - 1,
        region.col0 + region.cols - 1,
    )


def _assert_equivalent(grid, background: int, connectivity: int, single_color: bool) -> None:
    regions = interpreter._partition_objects(grid, connectivity, background, single_color)
    objects = segment_objects(grid, background, connectivity, single_color)
    assert len(regions) == len(objects), (
        f"connectivity={connectivity} single_color={single_color}: "
        f"{len(regions)} regions vs {len(objects)} objects"
    )
    for region, obj in zip(regions, objects):
        assert _region_bbox(region) == (obj.top, obj.left, obj.bottom, obj.right)
        cells, colors = _region_cells_and_colors(region)
        assert cells == obj.cells
        assert colors == obj.colors


def test_object_segmentation_matches_perception_module():
    for grid, background in GRIDS.values():
        for connectivity in (4, 8):
            for single_color in (True, False):
                _assert_equivalent(grid, background, connectivity, single_color)


def test_object_segmentation_reading_order_matches():
    """Both implementations discover components in the same raster scan,
    so a component's index in one list must name the same object as the
    same index in the other (no separate matching/sorting needed)."""
    grid, background = GRIDS["4conn_monochrome_bg0"]
    regions = interpreter._partition_objects(grid, 4, background, True)
    objects = segment_objects(grid, background, 4, True)
    assert [(_region_bbox(r)) for r in regions] == [
        (o.top, o.left, o.bottom, o.right) for o in objects
    ]
