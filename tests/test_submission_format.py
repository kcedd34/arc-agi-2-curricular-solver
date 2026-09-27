import pytest

from src.evaluation.submission_format import (
    build_submission,
    build_submission_from_predictions,
    validate_submission,
)
from src.utils.task_loader import Pair, Task


def _task(task_id, num_test_pairs=1):
    train = [Pair(input=[[1]], output=[[1]])]
    test = [Pair(input=[[i]], output=[[i]]) for i in range(num_test_pairs)]
    return Task(task_id=task_id, train=train, test=test)


def test_build_submission_fills_both_attempts_from_single_prediction():
    tasks = {"t1": _task("t1")}
    submission = build_submission(lambda task: [[[[5]]]], tasks)
    assert submission == {"t1": [{"attempt_1": [[5]], "attempt_2": [[5]]}]}


def test_build_submission_falls_back_to_input_copy_when_no_predictions():
    train = []
    test = [Pair(input=[[7]], output=[[7]])]
    tasks = {"t1": Task(task_id="t1", train=train, test=test)}
    submission = build_submission(lambda task: [[]], tasks)
    assert submission["t1"] == [{"attempt_1": [[7]], "attempt_2": [[7]]}]


def test_build_submission_fallback_attempt_2_uses_most_common_train_output():
    train = [
        Pair(input=[[1]], output=[[3]]),
        Pair(input=[[2]], output=[[3]]),
        Pair(input=[[4]], output=[[5]]),
    ]
    test = [Pair(input=[[8]], output=[[8]])]
    tasks = {"t1": Task(task_id="t1", train=train, test=test)}
    submission = build_submission(lambda task: [[]], tasks)
    assert submission["t1"] == [{"attempt_1": [[8]], "attempt_2": [[3]]}]


def test_build_submission_fallback_attempt_2_repeats_input_copy_when_no_clear_majority():
    train = [Pair(input=[[1]], output=[[3]]), Pair(input=[[2]], output=[[5]])]
    test = [Pair(input=[[8]], output=[[8]])]
    tasks = {"t1": Task(task_id="t1", train=train, test=test)}
    submission = build_submission(lambda task: [[]], tasks)
    assert submission["t1"] == [{"attempt_1": [[8]], "attempt_2": [[8]]}]


def test_build_submission_fallback_does_not_interfere_when_a_prediction_exists():
    train = [Pair(input=[[1]], output=[[9]]), Pair(input=[[2]], output=[[9]])]
    test = [Pair(input=[[7]], output=[[7]])]
    tasks = {"t1": Task(task_id="t1", train=train, test=test)}
    submission = build_submission(lambda task: [[[[5]]]], tasks)
    assert submission["t1"] == [{"attempt_1": [[5]], "attempt_2": [[5]]}]


def test_build_submission_preserves_test_pair_order_for_multi_test_tasks():
    tasks = {"t1": _task("t1", num_test_pairs=2)}
    submission = build_submission(lambda task: [[[[1]]], [[[2]]]], tasks)
    assert submission["t1"][0]["attempt_1"] == [[1]]
    assert submission["t1"][1]["attempt_1"] == [[2]]


def test_build_submission_from_predictions_matches_build_submission():
    tasks = {"t1": _task("t1", num_test_pairs=2)}
    predictions = {"t1": [[[[5]]], [[[6]]]]}
    submission = build_submission_from_predictions(predictions, tasks)
    assert submission["t1"][0]["attempt_1"] == [[5]]
    assert submission["t1"][1]["attempt_1"] == [[6]]


def test_build_submission_from_predictions_applies_fallback_when_empty():
    train = [Pair(input=[[1]], output=[[9]]), Pair(input=[[2]], output=[[9]])]
    test = [Pair(input=[[7]], output=[[7]])]
    tasks = {"t1": Task(task_id="t1", train=train, test=test)}
    submission = build_submission_from_predictions({"t1": [[]]}, tasks)
    assert submission["t1"] == [{"attempt_1": [[7]], "attempt_2": [[9]]}]


def test_validate_submission_accepts_well_formed_submission():
    tasks = {"t1": _task("t1")}
    submission = {"t1": [{"attempt_1": [[0]], "attempt_2": [[0]]}]}
    validate_submission(submission, tasks)  # must not raise


def test_validate_submission_rejects_missing_task_id():
    tasks = {"t1": _task("t1")}
    with pytest.raises(ValueError, match="missing task_id"):
        validate_submission({}, tasks)


def test_validate_submission_rejects_wrong_entry_count():
    tasks = {"t1": _task("t1", num_test_pairs=2)}
    submission = {"t1": [{"attempt_1": [[0]], "attempt_2": [[0]]}]}
    with pytest.raises(ValueError, match="expected 2 test entries"):
        validate_submission(submission, tasks)


def test_validate_submission_rejects_wrong_keys():
    tasks = {"t1": _task("t1")}
    submission = {"t1": [{"attempt_1": [[0]], "attempt_3": [[0]]}]}
    with pytest.raises(ValueError, match="attempt_1/attempt_2"):
        validate_submission(submission, tasks)


def test_validate_submission_rejects_invalid_grid_values():
    tasks = {"t1": _task("t1")}
    submission = {"t1": [{"attempt_1": [[0]], "attempt_2": [[10]]}]}
    with pytest.raises(ValueError, match="0-9"):
        validate_submission(submission, tasks)
