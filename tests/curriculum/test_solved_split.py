from dataclasses import dataclass

from src.curriculum.solved_split import SolvedSplit, count_split, format_split, ids_solved_at_2
from src.curriculum.verified_verdict import VerifiedVerdict


@dataclass
class _R:
    task_id: str
    solved: bool
    solved_at_1: bool


def test_count_split_separates_first_and_second_attempt_solves():
    results = [_R("a", True, True), _R("b", True, False), _R("c", False, False), _R("d", True, True)]
    assert count_split(results) == SolvedSplit(total=3, at1=2, at2=1)
    assert ids_solved_at_2(results) == ["b"]


def test_count_split_of_nothing_is_zero():
    assert count_split([]) == SolvedSplit(0, 0, 0)


def test_format_split_is_compact():
    assert format_split(SolvedSplit(7, 5, 2)) == "solved=7 (@1=5, @2=2)"


def test_verdict_properties_follow_attempt_matches():
    first = VerifiedVerdict("t", 2, 0, 2, False, True, True, None)
    second = VerifiedVerdict("t", 2, 0, 2, False, True, False, True)
    none = VerifiedVerdict("t", 2, 0, 2, False, False, False, False)
    assert (first.solved_at_1, first.solved_at_2) == (True, False)
    assert (second.solved_at_1, second.solved_at_2) == (False, True)
    assert (none.solved_at_1, none.solved_at_2) == (False, False)
