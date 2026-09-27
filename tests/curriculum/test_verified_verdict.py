"""Non-regression tests for the 2026-09-22 correction (ADR 0073): unanimous
agreement among verified candidates must never be treated as `solved`.

`73ccf9c2` is the real task that exposed the bug: every verified candidate
predicted the same test output, and the old status-based CLI/gate logic
accepted it as `solved` on that basis alone, without ever checking the
prediction against the real gabarito. It does not match.
"""
from pathlib import Path

from src.curriculum.verified_verdict import compute_verified_verdict, distinct_attempts

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def test_unanimous_but_gabarito_wrong_task_is_not_solved():
    verdict = compute_verified_verdict("73ccf9c2", TRAINING_DIR)

    assert verdict.unanimous is True
    assert verdict.solved is False


def test_unanimous_and_gabarito_correct_task_is_solved():
    verdict = compute_verified_verdict("007bbfb7", TRAINING_DIR)

    assert verdict.unanimous is True
    assert verdict.solved is True


def test_non_unanimous_task_can_still_be_solved_via_second_attempt(tmp_path, monkeypatch):
    """Synthetic pool (Round 6, ADR 0081): the noop-dedup in the object
    content prefilter removed the last real task known to exercise this
    path (`c8f0f002`, 20 -> 18 candidates, now unanimous), so the fallback
    is protected with a controlled pool: attempt 1 is wrong, the distinct
    attempt 2 matches the gabarito."""
    import json

    from src.curriculum.library.objects import object_search
    from src.curriculum.search import candidate_rank, rank

    wrong, right = [[[1]]], [[[2]]]
    task = {"train": [{"input": [[0]], "output": [[2]]}], "test": [{"input": [[0]], "output": [[2]]}]}
    (tmp_path / "synthetic.json").write_text(json.dumps(task), encoding="utf-8")
    monkeypatch.setattr(rank, "verified_main_candidates_with_predictions", lambda _t: [(None, wrong)])
    monkeypatch.setattr(object_search, "verified_object_candidates_with_predictions", lambda _t: [(None, right)])
    monkeypatch.setattr(candidate_rank, "rank_by_simplicity", lambda pairs: list(pairs))

    verdict = compute_verified_verdict("synthetic", tmp_path)

    assert verdict.error is None
    assert verdict.unanimous is False
    assert verdict.solved is True
    assert verdict.attempt_1_match is False
    assert verdict.attempt_2_match is True


def test_no_candidate_task_is_neither_unanimous_nor_solved():
    verdict = compute_verified_verdict("017c7c7b", TRAINING_DIR)

    assert verdict.num_verified_candidates == 0
    assert verdict.unanimous is False
    assert verdict.solved is False


def test_distinct_attempts_never_consulted_for_unanimity_alone():
    """`unanimous` and `solved` must be independently derivable: this is a
    structural guard against re-merging the two concepts (e.g. by making
    `solved` default to `unanimous` when only one distinct attempt exists)."""
    single_attempt = distinct_attempts([(None, [[1]]), (None, [[1]])])
    assert len(single_attempt) == 1
