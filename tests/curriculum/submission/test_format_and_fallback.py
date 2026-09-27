import pytest

from src.curriculum.loader import Task, TrainPair
from src.curriculum.submission.fallback import fallback_attempt_2
from src.curriculum.submission.format import build_entries, validate_submission

G1, G2, G3 = [[1, 1], [1, 1]], [[2, 2]], [[3]]


def _task(outputs=(G1, G2), tests=(G3, G3)):
    return Task("t", [TrainPair([[0]], o) for o in outputs], list(tests))


def test_fallback_attempt_2_unique_majority():
    assert fallback_attempt_2([G1, G1, G2], G3) == G1


def test_fallback_attempt_2_tie_or_single_uses_attempt_1():
    assert fallback_attempt_2([G1, G2], G3) == G3
    assert fallback_attempt_2([], G3) == G3


def test_no_attempts_falls_back_per_test_input():
    entries = build_entries(_task(), None)
    assert len(entries) == 2
    assert entries[0] == {"attempt_1": G3, "attempt_2": G3}


def test_one_attempt_is_reused_for_attempt_2():
    entries = build_entries(_task(), [[G1, G2]])
    assert entries[1] == {"attempt_1": G2, "attempt_2": G2}


def test_two_attempts_keep_order():
    entries = build_entries(_task(), [[G1, G1], [G2, G2]])
    assert entries[0] == {"attempt_1": G1, "attempt_2": G2}


def test_invalid_grid_in_attempt_falls_back():
    entries = build_entries(_task(), [[[[99]], G1]])
    assert entries[0]["attempt_1"] == G3


def test_validate_rejects_missing_and_extra_and_bad_shape():
    task = _task()
    good = {"t": build_entries(task, None)}
    validate_submission(good, {"t": task})
    with pytest.raises(ValueError):
        validate_submission({}, {"t": task})
    with pytest.raises(ValueError):
        validate_submission({"t": good["t"][:1]}, {"t": task})
    with pytest.raises(ValueError):
        validate_submission({"t": [{"attempt_1": G1}, {"attempt_1": G1}]}, {"t": task})
    with pytest.raises(ValueError):
        validate_submission({"t": [{"attempt_1": [[1.0]], "attempt_2": G1}] * 2}, {"t": task})
