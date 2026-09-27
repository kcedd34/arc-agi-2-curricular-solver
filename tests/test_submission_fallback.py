from src.evaluation.submission_fallback import fallback_attempt_1, fallback_attempt_2
from src.utils.task_loader import Pair


def test_fallback_attempt_1_copies_test_input():
    test_pair = Pair(input=[[3, 4], [5, 6]], output=[[0, 0], [0, 0]])
    assert fallback_attempt_1(test_pair) == [[3, 4], [5, 6]]


def test_fallback_attempt_2_uses_clearly_repeated_train_output():
    train = [Pair(input=[[1]], output=[[7]]), Pair(input=[[2]], output=[[7]]), Pair(input=[[3]], output=[[9]])]
    assert fallback_attempt_2(train, attempt_1=[[0]]) == [[7]]


def test_fallback_attempt_2_falls_back_to_attempt_1_when_all_outputs_distinct():
    train = [Pair(input=[[1]], output=[[7]]), Pair(input=[[2]], output=[[8]])]
    assert fallback_attempt_2(train, attempt_1=[[0]]) == [[0]]


def test_fallback_attempt_2_falls_back_to_attempt_1_on_tie():
    train = [Pair(input=[[1]], output=[[7]]), Pair(input=[[2]], output=[[7]]), Pair(input=[[3]], output=[[9]]), Pair(input=[[4]], output=[[9]])]
    assert fallback_attempt_2(train, attempt_1=[[0]]) == [[0]]


def test_fallback_attempt_2_falls_back_to_attempt_1_when_no_train_pairs():
    assert fallback_attempt_2([], attempt_1=[[0]]) == [[0]]
