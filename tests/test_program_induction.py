from src.solvers.neural.program_induction import apply_program_to_test, induce_verified_program
from src.utils.task_loader import Pair, Task

_IDENTITY_COMPLETION = "    return g\n"
_WRONG_COMPLETION = "    return [row[::-1] for row in g]\n"
_UNPARSEABLE_COMPLETION = "not indented, nothing to extract\n"


def _task_with_identity_rule():
    return Task(
        task_id="fixture",
        train=[
            Pair(input=[[1, 2]], output=[[1, 2]]),
            Pair(input=[[3, 4], [5, 6]], output=[[3, 4], [5, 6]]),
        ],
        test=[Pair(input=[[7, 8]], output=[[7, 8]])],
    )


def test_zero_survivors_when_no_completion_reproduces_the_train_pairs():
    task = _task_with_identity_rule()
    result = induce_verified_program([_WRONG_COMPLETION, _UNPARSEABLE_COMPLETION], task)
    assert result.verified_programs == []
    assert result.is_ambiguous is False
    assert result.chosen_program is None


def test_single_survivor_is_chosen_directly():
    task = _task_with_identity_rule()
    result = induce_verified_program([_WRONG_COMPLETION, _IDENTITY_COMPLETION], task)
    assert len(result.verified_programs) == 1
    assert result.is_ambiguous is False
    assert result.chosen_program is not None


def test_duplicate_completions_are_deduplicated_into_one_survivor():
    task = _task_with_identity_rule()
    result = induce_verified_program([_IDENTITY_COMPLETION, _IDENTITY_COMPLETION], task)
    assert len(result.verified_programs) == 1


def test_multiple_survivors_that_agree_on_every_test_input_are_not_ambiguous():
    # Textually different from identity but behaviorally identical: g is a
    # List[str] of row strings inside the sandbox, so this must preserve
    # each row as a string, not explode it into a list of characters.
    same_result_completion = "    return [row for row in g]\n"
    task = _task_with_identity_rule()
    result = induce_verified_program([_IDENTITY_COMPLETION, same_result_completion], task)
    assert len(result.verified_programs) == 2
    assert result.is_ambiguous is False
    assert result.chosen_program is not None


def test_multiple_survivors_that_disagree_on_a_test_input_are_ambiguous():
    task = Task(
        task_id="fixture",
        train=[Pair(input=[[1, 2]], output=[[1, 2]])],
        test=[Pair(input=[[3, 4]], output=[[3, 4]])],
    )
    # Hardcodes the single train pair as a List[str] row (the real shape g
    # has inside the sandbox), so it passes verification exactly like the
    # identity rule, but diverges from it on the held-out test input.
    hardcoded_special_case = (
        "    if g == [\"12\"]:\n"
        "        return [\"12\"]\n"
        "    return [\"99\"]\n"
    )
    result = induce_verified_program([_IDENTITY_COMPLETION, hardcoded_special_case], task)
    assert len(result.verified_programs) == 2
    assert result.is_ambiguous is True
    assert result.chosen_program is None


def test_apply_program_to_test_runs_the_program_on_every_test_pair_input():
    task = _task_with_identity_rule()
    program = "def transform(g):\n    return g\n"
    outputs = apply_program_to_test(program, task)
    assert outputs == [[[7, 8]]]
