"""End to end: a task whose rule is 'recolor the most isolated object' has no
handwritten selection that expresses it, and is found only through a
generated property when the discovery switch is on (ADR 0110)."""
from src.curriculum.discovery import task_generated
from src.curriculum.discovery.enumerate_gen import Entry
from src.curriculum.discovery.switch import ENV_VAR
from src.curriculum.library.derived.search import verified_derived_candidates_with_predictions
from src.curriculum.loader import Task, TrainPair

RECOLOR = 8


def _grid(size, cells):
    grid = [[0] * size for _ in range(size)]
    for r, c in cells:
        grid[r][c] = 1
    return grid


def _solved(grid, far):
    out = [row[:] for row in grid]
    out[far[0]][far[1]] = RECOLOR
    return out


def _pair(cells, far):
    grid = _grid(12, cells)
    return TrainPair(grid, _solved(grid, far))


def _task():
    train = [
        _pair([(2, 2), (2, 4), (8, 8)], (8, 8)),
        _pair([(3, 8), (3, 10), (9, 3)], (9, 3)),
        _pair([(5, 5), (6, 6), (5, 9), (9, 1)], (9, 1)),
    ]
    test = _grid(12, [(1, 1), (2, 3), (9, 9)])
    return Task("synthetic-isolated", train, [test])


def _gen_only(monkeypatch):
    entries = [Entry("min_dist", 1, 1, "int", False), Entry("size", 1, 1, "int", False)]
    monkeypatch.setattr(task_generated, "_entries", lambda: entries)


def _uses_generated(found):
    return [c for c, _ in found if "gen:" in c.describe()]


def test_generated_selection_solves_it_only_when_enabled(monkeypatch):
    _gen_only(monkeypatch)
    monkeypatch.delenv(ENV_VAR, raising=False)
    assert not _uses_generated(verified_derived_candidates_with_predictions(_task()))
    monkeypatch.setenv(ENV_VAR, "1")
    found = _uses_generated(verified_derived_candidates_with_predictions(_task()))
    assert found and "gen:min_dist" in found[0].describe()


def test_generated_prediction_is_the_expected_grid(monkeypatch):
    _gen_only(monkeypatch)
    monkeypatch.setenv(ENV_VAR, "1")
    task = _task()
    expected = _solved(task.test_inputs[0], (9, 9))
    hits = [p for c, p in verified_derived_candidates_with_predictions(task) if "gen:" in c.describe()]
    assert hits and hits[0][0] == expected
