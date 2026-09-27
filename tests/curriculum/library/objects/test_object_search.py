"""Unit tests for the object-pack gate-check search (staging, RN-CUR-36,
object-pack.md Section 5.5): enumeration reaches a task's true rule when
the object pack alone must find it (no teaching, no main-library help),
and the combined "check with the package" entry point returns the same
answer `search/rank.py::search_task` already returns whenever a task has
nothing to do with objects at all.
"""
from pathlib import Path

from src.curriculum.library.objects.object_search import (
    check_with_object_pack,
    enumerate_object_compositions,
    search_task_with_object_pack,
)
from src.curriculum.loader import Task, TrainPair, load_task
from src.curriculum.search.rank import search_task

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def _recolor_largest_object_task() -> Task:
    grid_in = [
        [0, 0, 0, 0, 0],
        [0, 5, 5, 0, 0],
        [0, 5, 5, 0, 0],
        [0, 0, 0, 3, 0],
        [0, 0, 0, 0, 0],
    ]
    grid_out = [
        [0, 0, 0, 0, 0],
        [0, 9, 9, 0, 0],
        [0, 9, 9, 0, 0],
        [0, 0, 0, 3, 0],
        [0, 0, 0, 0, 0],
    ]
    return Task(
        task_id="synthetic_recolor_largest",
        train=[TrainPair(input=grid_in, output=grid_out)],
        test_inputs=[grid_in],
    )


def test_search_task_with_object_pack_solves_recolor_largest_object():
    task = _recolor_largest_object_task()
    result = search_task_with_object_pack(task)
    assert result.status == "solved"
    assert result.predictions == [
        [
            [0, 0, 0, 0, 0],
            [0, 9, 9, 0, 0],
            [0, 9, 9, 0, 0],
            [0, 0, 0, 3, 0],
            [0, 0, 0, 0, 0],
        ]
    ]


def test_search_task_with_object_pack_solves_crop_to_largest_object():
    grid_in = [
        [0, 0, 0, 0, 0],
        [0, 3, 0, 0, 0],
        [0, 0, 0, 5, 0],
        [0, 0, 0, 5, 5],
        [0, 0, 0, 0, 0],
    ]
    task = Task(
        task_id="synthetic_crop_largest",
        train=[TrainPair(input=grid_in, output=[[5, 0], [5, 5]])],
        test_inputs=[grid_in],
    )
    result = search_task_with_object_pack(task)
    assert result.status == "solved"
    assert result.predictions == [[[5, 0], [5, 5]]]


def test_enumerate_object_compositions_is_empty_for_a_pure_scale_task():
    """A consistent-ratio tiling task (same shape as 007bbfb7's own
    scale-3 rule, scale-2 here): `same_shape` is false (absolute shapes
    differ per pair) but the row/col ratio is constant across pairs, so
    neither `should_include_identity_canvas` nor `should_include_crop_layout`
    applies (object-pack.md Section 3.6's `constant_shape_ratio` row)."""
    task = Task(
        task_id="synthetic_pure_scale",
        train=[
            TrainPair(input=[[0, 0]], output=[[0, 0, 0, 0], [0, 0, 0, 0]]),
            TrainPair(input=[[0, 0, 0]], output=[[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]),
        ],
        test_inputs=[[[0, 0]]],
    )
    assert list(enumerate_object_compositions(task)) == []


def _slide_and_erase_task() -> Task:
    """Largest object slides right to the border, the smaller one is
    erased: both content roles really write, so nothing survives the
    ADR 0080/0081 prefilter vacuously."""
    pairs = []
    for big_row, small in ((0, (5, 5)), (2, (5, 3))):
        grid_in = [[0] * 6 for _ in range(6)]
        for r in (big_row, big_row + 1):
            grid_in[r][0] = grid_in[r][1] = 5
        grid_in[small[0]][small[1]] = 3
        grid_out = [[0] * 6 for _ in range(6)]
        for r in (big_row, big_row + 1):
            grid_out[r][4] = grid_out[r][5] = 5
        pairs.append(TrainPair(input=grid_in, output=grid_out))
    return Task(task_id="synthetic_slide_erase", train=pairs, test_inputs=[pairs[0].input])


def test_no_identical_selected_and_not_selected_pair_object_pack():
    """Rodada 2 content x content pruning, object pack analog: a selector
    split where both branches emit the exact same steps is decorative
    (domain knowledge item 7) and must never be enumerated for
    `identity_canvas` (the only layout with a real not_selected branch;
    `crop_to_selected_object` has none)."""
    task = _slide_and_erase_task()
    compositions = list(enumerate_object_compositions(task))
    assert compositions
    assert not any(
        c.selected_content_name == c.not_selected_content_name
        and c.selected_content_params == c.not_selected_content_params
        for c in compositions
        if c.layout_name == "identity_canvas"
    )


def test_slide_selected_never_paired_with_itself():
    """Rodada 2 content x content pruning: `slide_selected` is by far the
    largest content piece (direction/stop/background), so pairing it
    with itself dominated this term's size in the Rodada 2 Fase A/B
    measurement across cap-hit tasks."""
    task = _slide_and_erase_task()
    compositions = list(enumerate_object_compositions(task))
    assert compositions
    assert not any(
        c.selected_content_name == "slide_selected" and c.not_selected_content_name == "slide_selected"
        for c in compositions
    )
    assert any(c.selected_content_name == "slide_selected" for c in compositions)


def test_content_background_param_matches_composition_background():
    """Rodada 4: `erase_selected`/`slide_selected`'s own `background` param
    must always equal the composition's own already-chosen `background`
    (ADR 0078's unified semantics: layout and content answer the same
    "what is this task's real background" question), never independently
    re-enumerated over `background_candidates(task)` (the pre-fix bug
    squared this factor's contribution with no semantic justification,
    ADR 0079). The synthetic task erases and slides for real, so the
    `background` param is actually enumerated and this is not vacuous."""
    task = _slide_and_erase_task()
    compositions = list(enumerate_object_compositions(task))
    assert compositions
    checked = 0
    for c in compositions:
        if c.layout_name != "identity_canvas":
            continue
        for params in (c.selected_content_params, c.not_selected_content_params):
            if "background" in params:
                assert params["background"] == c.background
                checked += 1
    assert checked > 0


def test_check_with_object_pack_matches_main_library_on_a_non_object_task():
    task = Task(
        task_id="synthetic_recolor_all",
        train=[
            TrainPair(input=[[0, 0]], output=[[7, 7]]),
            TrainPair(input=[[0]], output=[[7]]),
        ],
        test_inputs=[[[0, 0, 0]]],
    )
    combined = check_with_object_pack(task)
    plain = search_task(task)
    assert combined.status == plain.status
    assert combined.predictions == plain.predictions
