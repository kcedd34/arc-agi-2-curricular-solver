from src.solvers.neural.program_sandbox import run_program


def test_runs_a_simple_valid_program_and_returns_its_output():
    program = "def transform(g):\n    return g\n"
    assert run_program(program, ["12", "34"]) == ["12", "34"]


def test_returns_none_when_the_program_raises():
    program = "def transform(g):\n    raise ValueError('boom')\n"
    assert run_program(program, ["12"]) is None


def test_returns_none_when_transform_is_not_defined():
    program = "def not_transform(g):\n    return g\n"
    assert run_program(program, ["12"]) is None


def test_returns_none_when_the_result_is_not_a_list_of_strings():
    program = "def transform(g):\n    return 42\n"
    assert run_program(program, ["12"]) is None


def test_returns_none_on_timeout():
    program = "def transform(g):\n    while True:\n        pass\n"
    assert run_program(program, ["12"], timeout_seconds=0.5) is None


def test_denies_imports_inside_the_sandbox():
    program = "def transform(g):\n    import os\n    return g\n"
    assert run_program(program, ["12"]) is None


def test_allows_using_the_restricted_builtins():
    program = "def transform(g):\n    return [str(len(row)) for row in g]\n"
    assert run_program(program, ["12", "345"]) == ["2", "3"]
