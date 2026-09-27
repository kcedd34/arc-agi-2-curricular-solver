from src.solvers.connected_components import (
    Component,
    bounding_box,
    connected_regions,
    crop_to_bbox,
    find_color_components,
)


def test_connected_regions_groups_4_connected_true_cells():
    mask = [
        [True, True, False],
        [False, True, False],
        [False, False, True],
    ]
    regions = connected_regions(mask, connectivity=4)
    sizes = sorted(len(r) for r in regions)
    assert sizes == [1, 3]


def test_connected_regions_8_connected_merges_diagonal_cells():
    mask = [
        [True, False],
        [False, True],
    ]
    regions_4 = connected_regions(mask, connectivity=4)
    regions_8 = connected_regions(mask, connectivity=8)
    assert len(regions_4) == 2
    assert len(regions_8) == 1


def test_find_color_components_excludes_background_and_splits_by_color():
    grid = [
        [0, 1, 1],
        [0, 0, 2],
        [2, 0, 0],
    ]
    components = find_color_components(grid, connectivity=4, background=0)
    assert Component(color=1, cells=((0, 1), (0, 2))) in components
    assert Component(color=2, cells=((1, 2),)) in components
    assert Component(color=2, cells=((2, 0),)) in components
    assert len(components) == 3


def test_bounding_box_and_crop():
    cells = [(1, 2), (1, 3), (2, 2)]
    box = bounding_box(cells)
    assert box == (1, 2, 2, 3)
    grid = [[0, 0, 0, 0], [0, 0, 5, 6], [0, 0, 7, 0]]
    assert crop_to_bbox(grid, box) == [[5, 6], [7, 0]]
