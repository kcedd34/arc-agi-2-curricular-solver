from src.curriculum.perception.objects import (
    ObjectInstance,
    crop_to_bbox,
    infer_background,
    segment_objects,
    select_largest,
    select_smallest,
    select_unique_color,
)


def test_infer_background_most_frequent():
    grid = [[0, 0, 1], [0, 2, 2]]
    assert infer_background(grid) == 0


def test_infer_background_tie_breaks_to_lowest_color():
    grid = [[1, 1], [2, 2]]
    assert infer_background(grid) == 1


def test_segment_objects_4_connectivity_reading_order():
    grid = [
        [0, 1, 0, 2],
        [0, 1, 0, 2],
        [0, 0, 0, 0],
    ]
    objects = segment_objects(grid, background=0, connectivity=4)
    assert len(objects) == 2
    assert objects[0].color == 1
    assert objects[0].size == 2
    assert objects[1].color == 2
    assert objects[1].size == 2


def test_segment_objects_8_connectivity_merges_diagonal_touch():
    grid = [
        [1, 0],
        [0, 1],
    ]
    objs_4 = segment_objects(grid, background=0, connectivity=4)
    objs_8 = segment_objects(grid, background=0, connectivity=8)
    assert len(objs_4) == 2
    assert len(objs_8) == 1


def test_segment_objects_single_color_true_splits_by_color():
    grid = [[1, 2]]
    objects = segment_objects(grid, background=0, connectivity=4, single_color=True)
    assert len(objects) == 2


def test_segment_objects_single_color_false_groups_touching_colors():
    grid = [[1, 2]]
    objects = segment_objects(grid, background=0, connectivity=4, single_color=False)
    assert len(objects) == 1
    assert objects[0].colors == frozenset({1, 2})
    assert objects[0].color is None


def test_segment_objects_non_zero_background():
    grid = [
        [5, 5, 5],
        [5, 3, 5],
        [5, 5, 5],
    ]
    objects = segment_objects(grid, background=5, connectivity=4)
    assert len(objects) == 1
    assert objects[0].color == 3
    assert objects[0].top == 1 and objects[0].left == 1
    assert objects[0].bottom == 1 and objects[0].right == 1


def test_segment_objects_background_defaults_to_inferred():
    grid = [[0, 0, 1], [0, 0, 1]]
    objects = segment_objects(grid)
    assert len(objects) == 1
    assert objects[0].color == 1


def test_object_touches_border():
    grid = [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0],
    ]
    objects = segment_objects(grid, background=0)
    assert objects[0].touches_border(3, 3) is False

    grid2 = [
        [1, 0, 0],
        [0, 0, 0],
    ]
    objects2 = segment_objects(grid2, background=0)
    assert objects2[0].touches_border(2, 3) is True


def test_crop_to_bbox_fills_non_object_cells():
    grid = [
        [1, 0],
        [0, 1],
    ]
    objects = segment_objects(grid, background=0, connectivity=8, single_color=False)
    assert len(objects) == 1
    obj = objects[0]
    cropped = crop_to_bbox(grid, obj, fill=9)
    assert cropped == [[1, 9], [9, 1]]


def test_select_largest_returns_none_on_tie():
    a = ObjectInstance(frozenset({(0, 0)}), frozenset({1}), 0, 0, 0, 0)
    b = ObjectInstance(frozenset({(1, 1)}), frozenset({2}), 1, 1, 1, 1)
    assert select_largest([a, b]) is None


def test_select_largest_picks_unique_max():
    small = ObjectInstance(frozenset({(0, 0)}), frozenset({1}), 0, 0, 0, 0)
    big = ObjectInstance(
        frozenset({(1, 1), (1, 2)}), frozenset({2}), 1, 1, 1, 2
    )
    assert select_largest([small, big]) is big


def test_select_smallest_picks_unique_min():
    small = ObjectInstance(frozenset({(0, 0)}), frozenset({1}), 0, 0, 0, 0)
    big = ObjectInstance(
        frozenset({(1, 1), (1, 2)}), frozenset({2}), 1, 1, 1, 2
    )
    assert select_smallest([small, big]) is small


def test_select_largest_empty_list_is_none():
    assert select_largest([]) is None


def test_select_unique_color_picks_the_only_singleton_color():
    a = ObjectInstance(frozenset({(0, 0)}), frozenset({1}), 0, 0, 0, 0)
    b = ObjectInstance(frozenset({(1, 1)}), frozenset({1}), 1, 1, 1, 1)
    c = ObjectInstance(frozenset({(2, 2)}), frozenset({3}), 2, 2, 2, 2)
    assert select_unique_color([a, b, c]) is c


def test_select_unique_color_none_when_all_shared():
    a = ObjectInstance(frozenset({(0, 0)}), frozenset({1}), 0, 0, 0, 0)
    b = ObjectInstance(frozenset({(1, 1)}), frozenset({1}), 1, 1, 1, 1)
    assert select_unique_color([a, b]) is None


def test_select_unique_color_none_when_two_distinct_uniques_tie():
    a = ObjectInstance(frozenset({(0, 0)}), frozenset({1}), 0, 0, 0, 0)
    b = ObjectInstance(frozenset({(1, 1)}), frozenset({2}), 1, 1, 1, 1)
    assert select_unique_color([a, b]) is None
