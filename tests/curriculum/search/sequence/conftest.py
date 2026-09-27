import pytest

from src.curriculum.loader import Task, TrainPair

LAYOUTS = [
    [(0, 0, 3, 3), (5, 0, 2, 2), (7, 6, 1, 1)],
    [(0, 5, 2, 2), (4, 0, 3, 2), (8, 8, 1, 1)],
    [(1, 1, 3, 2), (6, 5, 2, 2), (0, 8, 1, 1)],
]
TEST_LAYOUT = [(0, 0, 2, 4), (4, 4, 2, 2), (8, 0, 1, 1)]


def _paint(layout, colors=None):
    grid = [[0] * 9 for _ in range(9)]
    sizes = [h * w for _r, _c, h, w in layout]
    for r, c, h, w in layout:
        color = 5
        if colors:
            color = 9 if h * w == max(sizes) else 8 if h * w == min(sizes) else 5
        for i in range(h):
            for j in range(w):
                grid[r + i][c + j] = color
    return grid


@pytest.fixture
def two_rule_task() -> Task:
    train = [TrainPair(_paint(layout), _paint(layout, colors=True)) for layout in LAYOUTS]
    return Task("synthetic_two_rule", train, [_paint(TEST_LAYOUT)])
