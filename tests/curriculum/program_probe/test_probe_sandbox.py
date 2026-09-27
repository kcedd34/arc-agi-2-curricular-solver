import pytest

from src.curriculum.program_probe.sandbox import run_program, static_problem

GRID = [[0, 1], [2, 0]]


def _run(code, seconds=1.0):
    return run_program(code, [GRID, GRID], seconds)


def test_identity_program_returns_the_grid():
    results = _run("def solve(grid):\n    return [row[:] for row in grid]\n")
    assert all(r.ok and r.grid == GRID for r in results)


def test_input_mutation_does_not_leak_between_calls():
    code = "def solve(grid):\n    grid[0][0] = 7\n    return grid\n"
    assert [r.grid[0][0] for r in _run(code)] == [7, 7]


def test_allowed_imports_work_and_others_fail():
    good = "from collections import Counter\nimport itertools, math\ndef solve(grid):\n    return grid\n"
    assert _run(good)[0].ok
    for module in ("os", "sys", "socket", "numpy", "subprocess"):
        assert not _run(f"import {module}\ndef solve(grid):\n    return grid\n")[0].ok


@pytest.mark.parametrize("code", [
    "def solve(grid):\n    return open('x').read()\n",
    "def solve(grid):\n    return eval('1')\n",
    "def solve(grid):\n    return grid.__class__\n",
])
def test_static_screen_refuses_dangerous_code(code):
    assert static_problem(code) is not None
    assert not _run(code)[0].ok


def test_exception_infinite_loop_and_malformed_output_are_failures_without_crash():
    boom = "def solve(grid):\n    return 1 / 0\n"
    loop = "def solve(grid):\n    while True:\n        pass\n"
    bad = "def solve(grid):\n    return [[1, 2], [3]]\n"
    out_of_range = "def solve(grid):\n    return [[10]]\n"
    for code in (boom, loop, bad, out_of_range, "def solve(grid) return", "x = 1\n"):
        assert not any(r.ok for r in _run(code))


def test_swallowing_the_alarm_still_ends_within_the_outer_timeout():
    code = "def solve(grid):\n    while True:\n        try:\n            while True:\n                pass\n        except:\n            pass\n"
    results = run_program(code, [GRID], 0.5)
    assert not results[0].ok


def test_memory_hog_is_contained():
    code = "def solve(grid):\n    return [[0] * (10 ** 10)]\n"
    assert not _run(code)[0].ok
