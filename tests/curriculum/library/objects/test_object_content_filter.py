"""Tests for the role-wise content prefilter (ADR 0080): it must drop
contents whose own write footprint contradicts the train outputs, and it
must never drop a content used by a verified full composition."""
from pathlib import Path

from src.curriculum.library.objects.object_content_filter import filter_content_for_role
from src.curriculum.library.objects.object_search import verified_object_candidates_with_predictions
from src.curriculum.loader import Task, TrainPair, load_task

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def _recolor_largest_task() -> Task:
    grid_in = [
        [0, 0, 0, 0, 0],
        [0, 5, 5, 0, 0],
        [0, 5, 5, 0, 0],
        [0, 0, 0, 3, 0],
        [0, 0, 0, 0, 0],
    ]
    grid_out = [row[:] for row in grid_in]
    for r in (1, 2):
        grid_out[r][1] = grid_out[r][2] = 9
    return Task("synthetic_recolor_largest", [TrainPair(grid_in, grid_out)], [grid_in])


def _filter(role, choices, task):
    return filter_content_for_role(role, choices, task, 4, True, 0, "largest_object", {})


def test_selected_role_keeps_only_the_recolor_that_matches_the_output():
    choices = [("keep", {}), ("recolor_selected", {"color": 9}), ("recolor_selected", {"color": 4})]
    survivors = _filter("selected", choices, _recolor_largest_task())
    assert ("recolor_selected", {"color": 9}) in survivors
    assert ("recolor_selected", {"color": 4}) not in survivors


def test_not_selected_role_drops_content_that_changes_the_untouched_object():
    choices = [("keep", {}), ("recolor_selected", {"color": 9}), ("erase_selected", {"background": 0})]
    survivors = _filter("not_selected", choices, _recolor_largest_task())
    assert survivors == [("keep", {})]


def test_content_that_writes_nothing_is_dropped_as_a_keep_duplicate():
    choices = [("keep", {}), ("hollow_selected", {"background": 0}), ("recolor_interior_selected", {"color": 9})]
    survivors = _filter("selected", choices, _recolor_largest_task())
    assert survivors == [("keep", {})]


def _assert_verified_contents_survive(task: Task) -> int:
    verified = verified_object_candidates_with_predictions(task)
    for composition, _predictions in verified:
        if getattr(composition, "layout_name", None) != "identity_canvas":
            continue
        args = (
            task, composition.connectivity, composition.single_color, composition.background,
            composition.selector_name, composition.selector_params,
        )
        selected = (composition.selected_content_name, composition.selected_content_params)
        not_selected = (composition.not_selected_content_name, composition.not_selected_content_params)
        assert selected in filter_content_for_role("selected", [selected], *args)
        assert not_selected in filter_content_for_role("not_selected", [not_selected], *args)
    return len(verified)


def test_every_verified_composition_survives_the_prefilter_synthetic():
    assert _assert_verified_contents_survive(_recolor_largest_task()) > 0


def test_every_verified_composition_survives_the_prefilter_real_tasks():
    for task_id in ("f341894c", "256b0a75", "b7955b3c"):
        _assert_verified_contents_survive(load_task(TRAINING_DIR / f"{task_id}.json"))
