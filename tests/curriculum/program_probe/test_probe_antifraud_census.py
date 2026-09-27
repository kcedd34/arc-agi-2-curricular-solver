import ast

from src.curriculum.program_probe.antifraud import audit, dimension_tests, embedded_grids
from src.curriculum.program_probe.census import DRAW, ERASE, MIXED, MOVE, RECOLOR, SHAPE, task_category

TRAIN = [[[0, 1, 0], [0, 0, 2], [3, 0, 0]], [[1, 1, 0], [0, 0, 2], [3, 0, 0]]]


def test_embedded_output_grid_is_flagged_and_matched_to_train():
    code = "def solve(grid):\n    return [[1, 1, 0], [0, 0, 2], [3, 0, 0]]\n"
    flags = audit(code, TRAIN)
    assert flags["embedded_known_grid"] == 1 and flags["suspicious"]


def test_dimension_conditional_is_flagged():
    code = "def solve(grid):\n    if len(grid) == 3:\n        return grid\n    return grid\n"
    assert dimension_tests(ast.parse(code)) == 1 and audit(code, TRAIN)["suspicious"]


def test_general_program_is_not_flagged():
    code = (
        "def solve(grid):\n    h, w = len(grid), len(grid[0])\n"
        "    return [[grid[r][c] or 1 for c in range(w)] for r in range(h)]\n"
    )
    flags = audit(code, TRAIN)
    assert not flags["suspicious"] and embedded_grids(ast.parse(code)) == []


def test_census_categories():
    assert task_category([([[0, 0]], [[1, 0]])]) == DRAW
    assert task_category([([[1, 0]], [[0, 0]])]) == ERASE
    assert task_category([([[1, 0]], [[2, 0]])]) == RECOLOR
    assert task_category([([[1, 0]], [[0, 1]])]) == MOVE
    assert task_category([([[1, 0]], [[0, 2]])]) == MIXED
    assert task_category([([[1, 0]], [[1, 0], [1, 0]])]) == SHAPE
