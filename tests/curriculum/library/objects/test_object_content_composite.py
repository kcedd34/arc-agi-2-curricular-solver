"""Composite object content (ADR 0086): fill holes + erase, fill holes + halo."""
from src.curriculum.library.objects.object_content_composite import COMPOSITE_PIECES
from src.curriculum.library.objects.object_content_registry import ALL_CONTENT_PIECES
from src.curriculum.library.objects.object_search import verified_object_candidates_with_predictions
from src.curriculum.loader import Task, TrainPair


def _frame(r, c, size=10):
    grid = [[0] * size for _ in range(size)]
    for dr in range(4):
        for dc in range(4):
            if dr in (0, 3) or dc in (0, 3):
                grid[r + dr][c + dc] = 2
    return grid


def _paint(grid, r, c, value, side=2):
    out = [row[:] for row in grid]
    for dr in range(side):
        for dc in range(side):
            out[r + dr][c + dc] = value
    return out


def _erase_task() -> Task:
    pairs = []
    for r, c in ((0, 0), (3, 4), (5, 1)):
        grid_in = _frame(r, c)
        blank = [[0] * 10 for _ in range(10)]
        pairs.append(TrainPair(grid_in, _paint(blank, r + 1, c + 1, 3)))
    return Task("synthetic_hole_erase", pairs, [pairs[0].input])


def _halo_task() -> Task:
    pairs = []
    for r, c in ((2, 2), (3, 4), (2, 1)):
        grid_in = _frame(r, c, 12)
        out = [row[:] for row in grid_in]
        for rr in range(r - 1, r + 5):
            for cc in range(c - 1, c + 5):
                if 0 <= rr < 12 and 0 <= cc < 12 and out[rr][cc] == 0 and not (r < rr < r + 3 and c < cc < c + 3):
                    out[rr][cc] = 7
        pairs.append(TrainPair(grid_in, _paint(out, r + 1, c + 1, 4)))
    return Task("synthetic_hole_halo", pairs, [pairs[0].input])


def _described(task):
    return [c.describe() for c, _ in verified_object_candidates_with_predictions(task)]


def test_registry_contains_base_and_composite_pieces():
    assert set(COMPOSITE_PIECES) <= set(ALL_CONTENT_PIECES)
    assert "fill_holes_selected" in ALL_CONTENT_PIECES


def test_search_finds_fill_holes_and_erase():
    assert any("fill_holes_erase_selected" in text for text in _described(_erase_task()))


def test_search_finds_fill_holes_and_halo():
    assert any("fill_holes_halo8_selected" in text for text in _described(_halo_task()))


def test_fill_holes_and_erase_is_not_found_when_the_frame_stays():
    task = _halo_task()
    assert not any("fill_holes_erase_selected" in text for text in _described(task))
