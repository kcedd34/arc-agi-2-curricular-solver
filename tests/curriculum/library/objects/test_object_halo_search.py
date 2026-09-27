"""End-to-end synthetic tests for the `objeto_halo` package (ADR 0084): the
object search finds halo compositions, and the halo content never touches
other objects."""
from src.curriculum.library.objects.object_search import verified_object_candidates_with_predictions
from src.curriculum.loader import Task, TrainPair


def _marker_grid(positions, size=9):
    grid = [[0] * size for _ in range(size)]
    for r, c in positions:
        grid[r][c] = 5
    return grid


def _ring(grid, r, c, diagonal):
    out = [row[:] for row in grid]
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if (dr, dc) == (0, 0) or (not diagonal and dr != 0 and dc != 0):
                continue
            if 0 <= r + dr < len(out) and 0 <= c + dc < len(out[0]):
                out[r + dr][c + dc] = 1
    return out


def _halo_task(diagonal: bool) -> Task:
    pairs = []
    for spot in ((2, 2), (5, 4), (3, 6)):
        grid_in = _marker_grid([spot])
        pairs.append(TrainPair(grid_in, _ring(grid_in, spot[0], spot[1], diagonal)))
    return Task("synthetic_halo", pairs, [pairs[0].input])


def _described(task: Task):
    return [c.describe() for c, _ in verified_object_candidates_with_predictions(task)]


def test_search_finds_halo8_composition():
    assert any("halo8_selected" in text for text in _described(_halo_task(True)))


def test_search_finds_halo4_composition():
    assert any("halo4_selected" in text for text in _described(_halo_task(False)))


def test_halo4_does_not_explain_a_diagonal_ring():
    assert not any("halo4_selected" in text for text in _described(_halo_task(True)))
