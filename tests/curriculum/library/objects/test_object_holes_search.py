"""End-to-end synthetic tests for the `topologia_dentro` package (ADR 0082):
the object search finds hole-filling compositions, and the new op/predicate
behave on their own."""
from src.curriculum.library.objects.object_search import verified_object_candidates_with_predictions
from src.curriculum.loader import Task, TrainPair
from src.curriculum.spec.interpreter import _fill_enclosed
from src.curriculum.spec._region_value import RegionValue

N = None


def _blank(n: int):
    return [[0] * n for _ in range(n)]


def _paint(grid, r0, c0, size, color, hole=False):
    for r in range(r0, r0 + size):
        for c in range(c0, c0 + size):
            grid[r][c] = color
    if hole:
        grid[r0 + size // 2][c0 + size // 2] = 0


def _fill_ring_task() -> Task:
    pairs = []
    for ring, solid in (((1, 1), (6, 6)), ((5, 1), (1, 6))):
        grid_in = _blank(10)
        _paint(grid_in, ring[0], ring[1], 3, 5, hole=True)
        _paint(grid_in, solid[0], solid[1], 3, 5)
        grid_out = [row[:] for row in grid_in]
        grid_out[ring[0] + 1][ring[1] + 1] = 4
        pairs.append(TrainPair(grid_in, grid_out))
    return Task("synthetic_fill_ring", pairs, [pairs[0].input])


def test_search_finds_fill_holes_composition():
    verified = verified_object_candidates_with_predictions(_fill_ring_task())
    described = [composition.describe() for composition, _ in verified]
    assert any("fill_holes_selected" in text for text in described)


def test_fill_enclosed_op_writes_only_holes():
    region = RegionValue(row0=2, col0=3, rows=3, cols=3, cells=[[1, 1, 1], [1, N, 1], [1, 1, 1]])
    out = _fill_enclosed(region, 7)
    assert out.cells == [[N, N, N], [N, 7, N], [N, N, N]]
    assert (out.row0, out.col0, out.rows, out.cols) == (2, 3, 3, 3)


def test_fill_enclosed_leaves_open_shapes_untouched():
    region = RegionValue(row0=0, col0=0, rows=3, cols=3, cells=[[1, N, 1], [1, N, 1], [1, 1, 1]])
    assert _fill_enclosed(region, 7).cells == [[N] * 3] * 3
