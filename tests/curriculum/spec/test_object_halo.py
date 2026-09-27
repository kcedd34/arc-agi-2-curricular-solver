"""Halo geometry and painting rule (ADR 0084)."""
from src.curriculum.spec._object_halo import halo_offsets, halo_region
from src.curriculum.spec._region_value import RegionValue


def _single_cell_region(row0: int, col0: int) -> RegionValue:
    return RegionValue(row0=row0, col0=col0, rows=1, cols=1, cells=[[5]])


def test_halo_offsets_four_neighbourhood_of_a_single_cell():
    assert halo_offsets([[5]], diagonal=False) == {(-1, 0), (1, 0), (0, -1), (0, 1)}


def test_halo_offsets_eight_neighbourhood_adds_corners():
    assert len(halo_offsets([[5]], diagonal=True)) == 8


def test_halo_offsets_exclude_member_cells():
    offsets = halo_offsets([[5, 5]], diagonal=False)
    assert (0, 0) not in offsets and (0, 1) not in offsets
    assert (0, -1) in offsets and (0, 2) in offsets


def test_halo_region_paints_only_background_cells_and_leaves_rest_none():
    grid = [[0] * 5 for _ in range(5)]
    grid[2][2] = 5
    region = halo_region(_single_cell_region(2, 2), color=1, diagonal=False, background=0, grid=grid)
    assert (region.row0, region.col0, region.rows, region.cols) == (1, 1, 3, 3)
    assert region.cells == [[None, 1, None], [1, None, 1], [None, 1, None]]


def test_halo_region_is_clipped_at_the_grid_border():
    grid = [[0] * 3 for _ in range(3)]
    grid[0][0] = 5
    region = halo_region(_single_cell_region(0, 0), color=1, diagonal=True, background=0, grid=grid)
    assert (region.row0, region.col0, region.rows, region.cols) == (0, 0, 2, 2)
    assert region.cells == [[None, 1], [1, 1]]


def test_halo_region_never_overwrites_another_object():
    grid = [[0] * 5 for _ in range(5)]
    grid[2][2] = 5
    grid[2][3] = 7
    region = halo_region(_single_cell_region(2, 2), color=1, diagonal=False, background=0, grid=grid)
    assert region.cells[1][2] is None
