from fractions import Fraction

from src.curriculum.loader import Task, TrainPair
from src.curriculum.perception.change_inventory import (
    build_pair_inventory,
    build_task_inventory,
)


def _task(pairs):
    return Task(task_id="synthetic", train=pairs, test_inputs=[])


def test_pair_inventory_basic_facts():
    pair = TrainPair(input=[[0, 1], [0, 0]], output=[[0, 2], [0, 0]])
    inv = build_pair_inventory(pair)
    assert inv.in_shape == (2, 2)
    assert inv.out_shape == (2, 2)
    assert inv.in_palette == frozenset({0, 1})
    assert inv.out_palette == frozenset({0, 2})
    assert inv.added_colors == frozenset({2})
    assert inv.removed_colors == frozenset({1})
    assert inv.changed_cells == 1
    assert inv.total_cells == 4


def test_pair_inventory_changed_cells_none_when_shapes_differ():
    pair = TrainPair(input=[[0, 1]], output=[[0, 1], [0, 0]])
    inv = build_pair_inventory(pair)
    assert inv.changed_cells is None
    assert inv.total_cells is None


def test_task_inventory_same_shape_true():
    pairs = [
        TrainPair(input=[[0, 1]], output=[[0, 2]]),
        TrainPair(input=[[1], [0]], output=[[2], [0]]),
    ]
    inv = build_task_inventory(_task(pairs))
    assert inv.same_shape is True
    assert inv.constant_shape_ratio is False
    assert inv.constant_out_shape is False
    assert inv.shape_depends_on_content is False


def test_task_inventory_few_cells_change_true_below_threshold():
    big_in = [[0] * 10 for _ in range(10)]
    big_out = [row[:] for row in big_in]
    big_out[0][0] = 1
    pairs = [TrainPair(input=big_in, output=big_out)]
    inv = build_task_inventory(_task(pairs))
    assert inv.same_shape is True
    assert inv.few_cells_change is True


def test_task_inventory_few_cells_change_false_above_threshold():
    big_in = [[0] * 10 for _ in range(10)]
    big_out = [[1] * 10 for _ in range(10)]
    pairs = [TrainPair(input=big_in, output=big_out)]
    inv = build_task_inventory(_task(pairs))
    assert inv.few_cells_change is False


def test_task_inventory_constant_shape_ratio_true_when_not_same_shape():
    pairs = [
        TrainPair(input=[[0, 1]], output=[[0, 1, 0, 1]]),
        TrainPair(input=[[1, 0], [0, 1]], output=[[1, 0, 1, 0], [0, 1, 0, 1]]),
    ]
    inv = build_task_inventory(_task(pairs))
    assert inv.same_shape is False
    assert inv.constant_shape_ratio is True
    assert inv.shape_depends_on_content is False


def test_task_inventory_constant_out_shape_true():
    pairs = [
        TrainPair(input=[[0, 1]], output=[[9, 9], [9, 9]]),
        TrainPair(input=[[1, 0, 1]], output=[[9, 9], [9, 9]]),
    ]
    inv = build_task_inventory(_task(pairs))
    assert inv.same_shape is False
    assert inv.constant_shape_ratio is False
    assert inv.constant_out_shape is True
    assert inv.shape_depends_on_content is False


def test_task_inventory_shape_depends_on_content_when_none_of_the_others_hold():
    pairs = [
        TrainPair(input=[[0, 1]], output=[[9, 9, 9]]),
        TrainPair(input=[[1, 0], [0, 1]], output=[[9]]),
    ]
    inv = build_task_inventory(_task(pairs))
    assert inv.same_shape is False
    assert inv.constant_shape_ratio is False
    assert inv.constant_out_shape is False
    assert inv.shape_depends_on_content is True


def test_task_inventory_no_new_colors_true_when_output_subset_of_input():
    pairs = [
        TrainPair(input=[[0, 1, 2]], output=[[1, 1, 0]]),
        TrainPair(input=[[2, 1, 0]], output=[[0, 0, 0]]),
    ]
    inv = build_task_inventory(_task(pairs))
    assert inv.no_new_colors is True
    assert inv.new_color_always_added is False


def test_task_inventory_new_color_always_added_true_on_common_added_color():
    pairs = [
        TrainPair(input=[[0, 1]], output=[[0, 5]]),
        TrainPair(input=[[1, 0]], output=[[5, 5]]),
    ]
    inv = build_task_inventory(_task(pairs))
    assert inv.no_new_colors is False
    assert inv.new_color_always_added is True


def test_task_inventory_object_count_preserved():
    pairs = [
        TrainPair(input=[[1, 0, 2]], output=[[2, 0, 1]]),
        TrainPair(input=[[0, 3, 0, 4]], output=[[4, 0, 3, 0]]),
    ]
    inv = build_task_inventory(_task(pairs))
    assert inv.object_count_preserved is True


def test_task_inventory_object_count_not_preserved():
    pairs = [TrainPair(input=[[1, 0, 2]], output=[[1, 1, 1]])]
    inv = build_task_inventory(_task(pairs))
    assert inv.object_count_preserved is False


def test_shape_ratio_uses_exact_fraction_not_float_drift():
    pair = TrainPair(input=[[0] * 3 for _ in range(3)], output=[[0] * 9 for _ in range(9)])
    inv = build_pair_inventory(pair)
    assert inv.shape_ratio == (Fraction(3, 1), Fraction(3, 1))
