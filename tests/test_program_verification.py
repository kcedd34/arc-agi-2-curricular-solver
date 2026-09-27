from src.solvers.neural.program_verification import (
    run_program_on_grid,
    verify_program_against_train_pairs,
)
from src.utils.task_loader import Pair


def test_run_program_on_grid_returns_the_transformed_grid():
    program = "def transform(g):\n    return g\n"
    assert run_program_on_grid(program, [[1, 2], [3, 4]]) == [[1, 2], [3, 4]]


def test_run_program_on_grid_returns_none_when_the_result_does_not_parse_as_a_grid():
    program = "def transform(g):\n    return ['ab', '']\n"
    assert run_program_on_grid(program, [[1, 2]]) is None


def test_verify_accepts_a_program_that_reproduces_every_train_pair():
    program = "def transform(g):\n    return g\n"
    train = [
        Pair(input=[[1, 2]], output=[[1, 2]]),
        Pair(input=[[3, 4], [5, 6]], output=[[3, 4], [5, 6]]),
    ]
    assert verify_program_against_train_pairs(program, train) is True


def test_verify_rejects_a_program_that_fails_on_any_train_pair():
    program = "def transform(g):\n    return g\n"
    train = [
        Pair(input=[[1, 2]], output=[[1, 2]]),
        Pair(input=[[3, 4]], output=[[9, 9]]),
    ]
    assert verify_program_against_train_pairs(program, train) is False


def test_verify_rejects_a_program_that_raises_on_any_train_pair():
    program = "def transform(g):\n    raise ValueError('boom')\n"
    train = [Pair(input=[[1, 2]], output=[[1, 2]])]
    assert verify_program_against_train_pairs(program, train) is False
