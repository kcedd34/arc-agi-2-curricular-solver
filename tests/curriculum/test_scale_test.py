"""Tests for scale_test.py's batch driver: parallel/sequential agreement
on real data (object-pack.md Section 5.7, item 1 of the 2026-09-22
follow-up request).

Deliberately does not use `SCALE_TEST_TASK_IDS` here: those 5 tasks are
picked precisely because they are the most expensive in the training
set (each hits the 5000-candidate object-pack cap, per
`docs/curriculum/tasks/object-pack.md` Section 5.7), and `_scale_worker`
additionally runs `build_search_log` plus a per-candidate cell-similarity
pass for every unsolved one - appropriate for the real scale-test run
(`scale_test.main`), not for a unit test invoked twice (sequential and
parallel) on every `pytest` run. A small, cheap real task exercises the
exact same `run_batch`-based code path without that cost."""
from src.curriculum.scale_test import run_scale_test


def test_run_scale_test_sequential_and_parallel_agree():
    sample = ["007bbfb7", "00576224"]
    sequential = run_scale_test(task_ids=sample, max_workers=1)
    parallel = run_scale_test(task_ids=sample, max_workers=4)

    assert [r.task_id for r in sequential] == [r.task_id for r in parallel]
    for seq_r, par_r in zip(sequential, parallel):
        assert seq_r.task_id == par_r.task_id
        assert seq_r.unanimous == par_r.unanimous
        assert seq_r.solved == par_r.solved
        assert seq_r.object_candidates_enumerated == par_r.object_candidates_enumerated
        assert seq_r.closest_hypothesis == par_r.closest_hypothesis
        assert seq_r.error is None
        assert par_r.error is None
