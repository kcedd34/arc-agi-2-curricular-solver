import pytest

from src.curriculum.library.panels.panel_composition import SUMMARY, SWAP, PanelComposition, build_panel_steps
from src.curriculum.library.panels.panel_enumerate import enumerate_panel_compositions
from src.curriculum.library.panels.panel_search import verified_panel_candidates_with_predictions
from src.curriculum.loader import Task, TrainPair
from src.curriculum.spec import interpreter, vocabulary as vocab
from src.curriculum.spec._expressions import InterpreterError
from src.curriculum.spec._panels import find_panels, summarize_uniform_panels, swap_panel_masks
from src.curriculum.spec._region_value import RegionValue


def _region(cells):
    return RegionValue(row0=0, col0=0, rows=len(cells), cols=len(cells[0]), cells=cells)


def test_find_panels_uses_full_lines():
    grid = [[1, 1, 0, 2], [0, 0, 0, 0], [3, 3, 0, 4]]
    assert find_panels(grid) == ([(0, 1), (2, 3)], [(0, 2), (3, 4)])


def test_find_panels_none_without_lines():
    assert find_panels([[1, 2], [3, 4]]) is None


def test_summary_takes_bbox_of_uniform_panels():
    grid = [[1, 1, 0, 5, 6], [1, 1, 0, 6, 5], [0, 0, 0, 0, 0], [7, 7, 0, 2, 2], [7, 7, 0, 2, 2]]
    out = summarize_uniform_panels(_region(grid), vocab.PanelSummary(9))
    assert out.cells == [[1, 9], [7, 2]]


def test_summary_fills_non_uniform_inside_box_and_ignores_outside():
    grid = [[3, 3, 0, 1, 2, 0, 4, 4], [3, 3, 0, 2, 1, 0, 4, 4]]
    grid += [[0] * 8]
    grid += [[1, 2, 0, 5, 5, 0, 1, 2], [2, 1, 0, 5, 5, 0, 2, 1]]
    out = summarize_uniform_panels(_region(grid), vocab.PanelSummary(9))
    assert out.cells == [[3, 9, 4], [9, 5, 9]]


def test_swap_exact_result():
    grid = [[1, 2, 0, 3, 3], [1, 1, 0, 3, 4]]
    grid += [[0] * 5, [1, 1, 0, 3, 3]]
    out = swap_panel_masks(_region(grid), vocab.PanelSwap("row")).cells
    assert out[0] == [1, 1, 0, 3, 1]
    assert out[1] == [1, 3, 0, 3, 3]
    assert out[3] == [1, 1, 0, 3, 3]


def test_swap_rejects_axis_without_two_panels():
    grid = [[1, 0, 2, 0, 3], [1, 0, 2, 0, 3], [0] * 5, [1, 0, 2, 0, 3]]
    with pytest.raises(InterpreterError):
        swap_panel_masks(_region(grid), vocab.PanelSwap("row"))


def _summary_task():
    a = [[1, 1, 0, 4, 5], [1, 1, 0, 5, 4], [0] * 5, [6, 6, 0, 4, 5], [6, 6, 0, 5, 4]]
    b = [[2, 2, 0, 3, 3], [2, 2, 0, 3, 3], [0] * 5, [4, 5, 0, 8, 8], [5, 4, 0, 8, 8]]
    return Task("synthetic", [TrainPair(a, [[1], [6]]), TrainPair(b, [[2, 3], [0, 8]])], [a])


def test_summary_candidate_verifies_on_synthetic_task():
    found = verified_panel_candidates_with_predictions(_summary_task())
    assert any(c.mode == SUMMARY and c.fill == 0 for c, _ in found)


def test_no_candidates_without_separators():
    task = Task("plain", [TrainPair([[1, 2], [3, 4]], [[1, 2], [3, 4]])], [[[1, 2], [3, 4]]])
    assert list(enumerate_panel_compositions(task)) == []


def test_steps_run_through_interpreter():
    grid = [[1, 1, 0, 3, 3], [0] * 5, [1, 1, 0, 3, 3]]
    steps = build_panel_steps(PanelComposition(SWAP, "row", 0))
    out, _trace = interpreter.run(steps, grid)
    assert out == grid
