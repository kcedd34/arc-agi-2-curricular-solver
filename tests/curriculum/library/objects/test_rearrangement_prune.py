"""ADR 0092: rearrangement tasks keep all connectivity combos."""
from src.curriculum.library.objects import object_params
from src.curriculum.library.objects.object_rearrangement import is_rearrangement_task
from src.curriculum.loader import Task, TrainPair


def _task(*pairs):
    return Task("t", [TrainPair(i, o) for i, o in pairs], [])


GRAVITY = _task(([[1, 0], [0, 0], [2, 0]], [[0, 0], [1, 0], [2, 0]]))
RECOLOR = _task(([[1, 0], [0, 0]], [[3, 0], [0, 0]]))
IDENTITY = _task(([[1, 0]], [[1, 0]]))
RESIZE = _task(([[1, 0]], [[1, 0, 0]]))


def test_pure_movement_is_rearrangement():
    assert is_rearrangement_task(GRAVITY)


def test_recolor_identity_resize_and_empty_are_not():
    assert not is_rearrangement_task(RECOLOR)
    assert not is_rearrangement_task(IDENTITY)
    assert not is_rearrangement_task(RESIZE)
    assert not is_rearrangement_task(_task())


def test_rearrangement_keeps_all_four_combos():
    combos = object_params.connectivity_single_color_candidates(GRAVITY)
    assert len(combos) == 4


def test_non_rearrangement_still_pruned_by_object_count():
    combos = object_params.connectivity_single_color_candidates(RECOLOR)
    assert combos == [c for c in combos if object_params._object_count_matches(RECOLOR, *c)]
