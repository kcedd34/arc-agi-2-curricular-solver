"""Corner-marker action of the derived family (Round 20, ADR 0108): a region
takes the colour of the marker on its top-left junction and the marker resets."""
from src.curriculum.library.derived.enumerate import derived_hypothesis_counts
from src.curriculum.library.derived.search import verified_derived_candidates_with_predictions
from src.curriculum.loader import Task, TrainPair

WALL = 8


def _rooms_pair(rooms):
    """`rooms`: (row0, col0, rows, cols, marker); the marker sits on (row0-1, col0-1)."""
    grid = [[WALL] * 12 for _ in range(12)]
    out = [row[:] for row in grid]
    for r0, c0, h, w, marker in rooms:
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                grid[r][c] = 0
                out[r][c] = marker
        grid[r0 - 1][c0 - 1] = marker
        out[r0 - 1][c0 - 1] = 0
    return TrainPair(grid, out)


def _task():
    train = [
        _rooms_pair([(1, 1, 2, 3, 4), (5, 5, 3, 2, 0)]),
        _rooms_pair([(2, 2, 3, 3, 6), (7, 7, 2, 2, 4)]),
        _rooms_pair([(1, 6, 2, 2, 6), (6, 1, 3, 4, 0), (8, 8, 2, 2, 4)]),
    ]
    test_pair = _rooms_pair([(2, 1, 3, 2, 4), (6, 6, 2, 3, 6)])
    return Task("rooms", train, [test_pair.input]), test_pair


def _corner_hits(task):
    found = verified_derived_candidates_with_predictions(task)
    return [(c, p) for c, p in found if "recolor_clear_corner_nw(corner_marker:" in c.describe()]


def test_corner_marker_action_recolors_rooms_and_resets_markers():
    task, test_pair = _task()
    hits = _corner_hits(task)
    assert hits and all(preds == [test_pair.output] for _, preds in hits)


def test_corner_marker_is_pruned_when_no_marker_cell_changes():
    train = [TrainPair([[0, 0], [0, 0]], [[3, 3], [3, 3]])]
    task = Task("no-marker", train, [[[0, 0], [0, 0]]])
    assert not _corner_hits(task)


def test_pruning_keeps_the_corner_family_small_on_the_synthetic_task():
    task, _ = _task()
    counts = derived_hypothesis_counts(task)
    assert counts.after < counts.before // 100
