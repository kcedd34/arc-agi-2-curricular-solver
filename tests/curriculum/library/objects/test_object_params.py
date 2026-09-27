"""Unit tests for the object-pack parameter inference module (staging,
RN-CUR-36, object-pack.md Section 3.5/3.6, ADR 0070): synthetic-grid
coverage for the object-pack-specific rules (slide direction,
connectivity/single_color, crop/identity-canvas layout eligibility).
The two color-candidate wrappers reuse `search/pruning.py`'s already-
tested generic functions, so are covered here only as pass-through
smoke tests.
"""
from src.curriculum.library.objects.object_params import (
    background_candidates,
    connectivity_single_color_candidates,
    objects_of_color_candidates,
    recolor_target_color_candidates,
    should_include_crop_layout,
    should_include_identity_canvas,
    slide_direction_candidates,
)
from src.curriculum.loader import Task, TrainPair


def test_recolor_target_color_candidates_delegates_to_pruning():
    task = Task(
        task_id="synthetic",
        train=[TrainPair(input=[[0, 0]], output=[[7, 7]])],
        test_inputs=[[[0, 0]]],
    )
    assert recolor_target_color_candidates(task) == [7]


def test_background_candidates_delegates_to_pruning():
    task = Task(
        task_id="synthetic",
        train=[TrainPair(input=[[2, 2, 5]], output=[[2, 2, 5]])],
        test_inputs=[[[2, 2, 5]]],
    )
    assert background_candidates(task) == [2, 5]


def test_objects_of_color_candidates_delegates_to_pruning():
    task = Task(
        task_id="synthetic",
        train=[
            TrainPair(input=[[1, 2]], output=[[1, 2]]),
            TrainPair(input=[[2, 3]], output=[[2, 3]]),
        ],
        test_inputs=[[[2]]],
    )
    assert objects_of_color_candidates(task) == [2]


def test_slide_direction_candidates_infers_right_from_consistent_displacement():
    task = Task(
        task_id="synthetic",
        train=[
            TrainPair(input=[[5, 0, 0, 0]], output=[[0, 5, 0, 0]]),
            TrainPair(input=[[0, 5, 0, 0]], output=[[0, 0, 5, 0]]),
        ],
        test_inputs=[[[5, 0, 0, 0]]],
    )
    assert slide_direction_candidates(task) == ["right"]


def test_slide_direction_candidates_falls_back_to_all_4_when_pairs_disagree():
    task = Task(
        task_id="synthetic",
        train=[
            TrainPair(input=[[5, 0, 0, 0]], output=[[0, 5, 0, 0]]),  # right
            TrainPair(input=[[0, 0, 0, 5]], output=[[0, 0, 5, 0]]),  # left
        ],
        test_inputs=[[[5, 0, 0, 0]]],
    )
    assert slide_direction_candidates(task) == ["up", "down", "left", "right"]


def test_slide_direction_candidates_falls_back_when_more_than_one_object():
    task = Task(
        task_id="synthetic",
        train=[TrainPair(input=[[5, 0, 3, 0]], output=[[0, 5, 3, 0]])],
        test_inputs=[[[5, 0, 3, 0]]],
    )
    assert slide_direction_candidates(task) == ["up", "down", "left", "right"]


def test_connectivity_single_color_candidates_prunes_combos_with_wrong_object_count():
    """5 and 3 sit side by side: single_color=True sees 2 objects there,
    single_color=False merges them into 1. The output is a single
    same-colored block either way, so only the single_color=False combos
    (whose input/output counts both come out to 1) survive."""
    grid_in = [[0, 5, 3, 0], [0, 0, 0, 0]]
    grid_out = [[0, 7, 7, 0], [0, 0, 0, 0]]
    task = Task(
        task_id="synthetic",
        train=[TrainPair(input=grid_in, output=grid_out)],
        test_inputs=[grid_in],
    )
    combos = connectivity_single_color_candidates(task)
    assert (4, False) in combos
    assert (8, False) in combos
    assert (4, True) not in combos
    assert (8, True) not in combos


def test_connectivity_single_color_candidates_falls_back_to_all_4_when_none_match():
    grid_in = [[5, 0, 3]]
    grid_out = [[5, 0, 3], [0, 0, 0], [0, 0, 8]]
    task = Task(
        task_id="synthetic",
        train=[TrainPair(input=grid_in, output=grid_out)],
        test_inputs=[grid_in],
    )
    combos = connectivity_single_color_candidates(task)
    assert combos == [(4, True), (4, False), (8, True), (8, False)]


def test_should_include_identity_canvas_true_when_same_shape():
    task = Task(
        task_id="synthetic",
        train=[TrainPair(input=[[0, 0]], output=[[5, 5]])],
        test_inputs=[[[0, 0]]],
    )
    assert should_include_identity_canvas(task) is True


def test_should_include_identity_canvas_false_when_shape_changes():
    task = Task(
        task_id="synthetic",
        train=[TrainPair(input=[[0, 0]], output=[[5]])],
        test_inputs=[[[0, 0]]],
    )
    assert should_include_identity_canvas(task) is False


def test_should_include_crop_layout_true_for_constant_out_shape_smaller_than_input():
    task = Task(
        task_id="synthetic",
        train=[
            TrainPair(input=[[0, 0, 0], [0, 5, 0]], output=[[5]]),
            TrainPair(input=[[0, 0], [0, 3]], output=[[3]]),
        ],
        test_inputs=[[[0, 0, 0], [0, 5, 0]]],
    )
    assert should_include_crop_layout(task) is True


def test_should_include_crop_layout_false_when_same_shape():
    task = Task(
        task_id="synthetic",
        train=[TrainPair(input=[[0, 0]], output=[[5, 5]])],
        test_inputs=[[[0, 0]]],
    )
    assert should_include_crop_layout(task) is False
