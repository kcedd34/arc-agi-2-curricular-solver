"""Unit tests for search/pruning.py (RN-CUR-33 step 3): factor-per-axis,
palette, and layout/selector compatibility inference, on both a tiny
synthetic task and the two real solved tasks."""
from pathlib import Path

from src.curriculum.loader import Task, TrainPair, load_task
from src.curriculum.search.pruning import (
    infer_colors_common_to_every_input,
    infer_consistent_axis_scale,
    infer_palette,
    infer_target_color_candidates,
    layout_matches_input_dims,
)

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def test_infer_consistent_axis_scale_agrees_across_pairs():
    task = load_task(TRAINING_DIR / "007bbfb7.json")
    assert infer_consistent_axis_scale(task, "row") == 3
    assert infer_consistent_axis_scale(task, "col") == 3


def test_infer_consistent_axis_scale_none_when_pairs_disagree():
    task = Task(
        task_id="synthetic",
        train=[
            TrainPair(input=[[0]], output=[[0], [0]]),  # row scale 2
            TrainPair(input=[[0]], output=[[0], [0], [0]]),  # row scale 3
        ],
        test_inputs=[[[0]]],
    )
    assert infer_consistent_axis_scale(task, "row") is None


def test_infer_consistent_axis_scale_none_when_not_divisible():
    task = Task(
        task_id="synthetic",
        train=[TrainPair(input=[[0, 0]], output=[[0, 0, 0]])],
        test_inputs=[[[0, 0]]],
    )
    assert infer_consistent_axis_scale(task, "col") is None


def test_infer_palette_matches_observed_colors_only():
    task = load_task(TRAINING_DIR / "00576224.json")
    palette = infer_palette(task)
    assert set(palette) == {3, 4, 6, 7, 8, 9}
    assert 0 not in palette


def test_layout_matches_input_dims_true_for_007bbfb7_own_scale():
    task = load_task(TRAINING_DIR / "007bbfb7.json")
    assert layout_matches_input_dims(task, 3, 3) is True


def test_layout_matches_input_dims_false_for_00576224_own_scale():
    task = load_task(TRAINING_DIR / "00576224.json")
    assert layout_matches_input_dims(task, 3, 3) is False
    assert layout_matches_input_dims(task, 2, 2) is True


def test_infer_target_color_restricted_to_colors_common_to_every_pairs_added_set():
    task = Task(
        task_id="synthetic",
        train=[
            TrainPair(input=[[0, 0]], output=[[5, 9]]),  # added {5, 9}
            TrainPair(input=[[0, 0]], output=[[9, 9]]),  # added {9}
        ],
        test_inputs=[[[0, 0]]],
    )
    assert infer_target_color_candidates(task) == [9]


def test_infer_target_color_falls_back_to_output_colors_when_no_color_is_always_added():
    task = Task(
        task_id="synthetic",
        train=[
            TrainPair(input=[[5, 0]], output=[[5, 0]]),  # nothing added
            TrainPair(input=[[0, 0]], output=[[0, 0]]),
        ],
        test_inputs=[[[0, 0]]],
    )
    assert infer_target_color_candidates(task) == [0, 5]


def test_infer_colors_common_to_every_input_is_the_intersection():
    task = Task(
        task_id="synthetic",
        train=[
            TrainPair(input=[[1, 2]], output=[[1, 2]]),
            TrainPair(input=[[2, 3]], output=[[2, 3]]),
        ],
        test_inputs=[[[2]]],
    )
    assert infer_colors_common_to_every_input(task) == [2]
