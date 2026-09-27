"""End-to-end synthetic tests for the `objeto_contorno` package (ADR 0081):
the object search must find compositions built from the new border/
interior pieces on tasks that no pre-existing piece can express."""
from src.curriculum.library.objects.object_search import verified_object_candidates_with_predictions
from src.curriculum.loader import Task, TrainPair


def _blank(rows: int, cols: int):
    return [[0] * cols for _ in range(rows)]


def _paint(grid, r0, c0, rows, cols, color):
    for r in range(r0, r0 + rows):
        for c in range(c0, c0 + cols):
            grid[r][c] = color


def _border_recolor_task() -> Task:
    pairs = []
    for spots in (((1, 1), (5, 5)), ((0, 4), (4, 0))):
        grid_in = _blank(9, 9)
        for r0, c0 in spots:
            _paint(grid_in, r0, c0, 3, 3, 5)
        grid_out = [row[:] for row in grid_in]
        for r0, c0 in spots:
            _paint(grid_out, r0, c0, 3, 3, 2)
            grid_out[r0 + 1][c0 + 1] = 5
        pairs.append(TrainPair(grid_in, grid_out))
    return Task("synthetic_border_recolor", pairs, [pairs[0].input])


def _hollow_thick_objects_task() -> Task:
    pairs = []
    for block, line in (((1, 1), (6, 1)), ((5, 5), (1, 1))):
        grid_in = _blank(9, 9)
        _paint(grid_in, block[0], block[1], 3, 3, 5)
        _paint(grid_in, line[0], line[1], 1, 4, 5)
        grid_out = [row[:] for row in grid_in]
        grid_out[block[0] + 1][block[1] + 1] = 0
        pairs.append(TrainPair(grid_in, grid_out))
    return Task("synthetic_hollow_thick", pairs, [pairs[0].input])


def _content_names(task: Task):
    verified = verified_object_candidates_with_predictions(task)
    return {
        name
        for composition, _ in verified
        if hasattr(composition, "selected_content_name")
        for name in (composition.selected_content_name, composition.not_selected_content_name)
    }


def test_search_finds_border_recolor_composition():
    assert "recolor_border_selected" in _content_names(_border_recolor_task())


def test_search_finds_hollow_on_objects_with_interior():
    verified = verified_object_candidates_with_predictions(_hollow_thick_objects_task())
    described = [composition.describe() for composition, _ in verified]
    assert any("hollow_selected" in text or "recolor_interior_selected" in text for text in described)
