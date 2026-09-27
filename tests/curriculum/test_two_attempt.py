"""Unit tests for the two-attempt policy driver (item 3 of the
2026-09-22 follow-up request, RN-CUR-04)."""
from pathlib import Path

from src.curriculum.two_attempt import (
    TwoAttemptResult,
    _distinct_attempts,
    format_report,
    run_two_attempt_check,
)

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")
SAMPLE_TASK_IDS = ["007bbfb7", "00576224", "009d5c81", "00d62c1b", "00dbd492"]


def test_distinct_attempts_skips_redundant_confirmations():
    ranked = [(None, [[1]]), (None, [[1]]), (None, [[2]])]
    assert _distinct_attempts(ranked) == [[[1]], [[2]]]


def test_distinct_attempts_returns_single_attempt_when_all_agree():
    ranked = [(None, [[1]]), (None, [[1]])]
    assert _distinct_attempts(ranked) == [[[1]]]


def test_distinct_attempts_empty_when_no_candidates():
    assert _distinct_attempts([]) == []


def test_run_two_attempt_check_sequential_and_parallel_agree_on_real_tasks():
    sequential = run_two_attempt_check(SAMPLE_TASK_IDS, training_dir=TRAINING_DIR, max_workers=1)
    parallel = run_two_attempt_check(SAMPLE_TASK_IDS, training_dir=TRAINING_DIR, max_workers=4)

    assert sequential == parallel
    assert [r.task_id for r in sequential] == SAMPLE_TASK_IDS
    assert all(r.error is None for r in sequential)


def test_format_report_lists_resolved_tasks_and_detail():
    results = [
        TwoAttemptResult("a", num_verified_candidates=2, attempt_1_match=False, attempt_2_match=True, resolved=True),
        TwoAttemptResult("b", num_verified_candidates=1, attempt_1_match=False, attempt_2_match=None, resolved=False),
    ]
    report = format_report(results)

    assert "Now resolved (attempt_1 or attempt_2 matches gabarito): 1" in report
    assert "  - a" in report
    assert "a: num_verified=2 attempt_1=False attempt_2=True resolved=True" in report
