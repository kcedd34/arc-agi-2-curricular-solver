"""ADR 0090: the caches and shared prefilter results only change time, never
the enumerated compositions."""
from src.curriculum.library.objects import object_search
from src.curriculum.library.objects._task_cache import cached_for_task, clear_task_cache
from src.curriculum.library.objects.object_selection_signature import selection_signature
from src.curriculum.loader import Task, TrainPair


def _task() -> Task:
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


def _copy(task: Task) -> Task:
    train = [TrainPair([r[:] for r in p.input], [r[:] for r in p.output]) for p in task.train]
    return Task(task.task_id, train, [[r[:] for r in g] for g in task.test_inputs])


def test_task_cache_is_keyed_by_content_not_identity():
    clear_task_cache()
    calls = []
    first = cached_for_task(_task(), "x", lambda: calls.append(1) or [1])
    second = cached_for_task(_copy(_task()), "x", lambda: calls.append(1) or [2])
    assert first is second and len(calls) == 1


def test_task_cache_rebuilds_for_a_different_task():
    clear_task_cache()
    other = Task("other", [TrainPair([[1]], [[2]])], [[[1]]])
    assert cached_for_task(_task(), "x", lambda: "a") == "a"
    assert cached_for_task(other, "x", lambda: "b") == "b"


def test_enumeration_is_repeatable_and_cached():
    clear_task_cache()
    first = [c.describe() for c in object_search.enumerate_object_compositions(_task())]
    second = [c.describe() for c in object_search.enumerate_object_compositions(_copy(_task()))]
    assert first == second and first


def test_selectors_with_identical_routing_share_a_signature():
    task = _task()
    args = (task, 4, True, 0)
    largest = selection_signature(*args, "largest_object", {})
    color5 = selection_signature(*args, "objects_of_color", {"color": 5})
    color3 = selection_signature(*args, "objects_of_color", {"color": 3})
    assert largest == color5
    assert largest != color3


def test_signature_sharing_does_not_change_the_enumerated_compositions(monkeypatch):
    clear_task_cache()
    shared = [c.describe() for c in object_search.enumerate_object_compositions(_task())]
    clear_task_cache()
    monkeypatch.setattr(object_search, "selection_signature", lambda *a, **k: None)
    unshared = [c.describe() for c in object_search.enumerate_object_compositions(_task())]
    assert shared == unshared
