"""Unit tests for the candidate-choice hit-rate driver (item 2 of the
2026-09-22 follow-up request)."""
from pathlib import Path

from src.curriculum.candidate_hit_rate import (
    HitRateTaskResult,
    format_report,
    run_hit_rate_analysis,
    summarize,
)

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")
SAMPLE_TASK_IDS = ["007bbfb7", "00576224", "009d5c81", "00d62c1b", "00dbd492"]


def test_run_hit_rate_analysis_sequential_and_parallel_agree_on_real_tasks():
    sequential = run_hit_rate_analysis(SAMPLE_TASK_IDS, training_dir=TRAINING_DIR, max_workers=1)
    parallel = run_hit_rate_analysis(SAMPLE_TASK_IDS, training_dir=TRAINING_DIR, max_workers=4)

    assert sequential == parallel
    assert [r.task_id for r in sequential] == SAMPLE_TASK_IDS
    assert all(r.error is None for r in sequential)


def test_summarize_rates_are_computed_only_over_tasks_with_candidates():
    results = [
        HitRateTaskResult("a", num_verified_candidates=0, top1_match=None, top2_match=None),
        HitRateTaskResult("b", num_verified_candidates=1, top1_match=True, top2_match=True),
        HitRateTaskResult("c", num_verified_candidates=2, top1_match=False, top2_match=True),
    ]
    summary = summarize(results)

    assert summary["n_tasks_with_candidates"] == 2
    assert summary["top1_rate"] == 0.5
    assert summary["top2_rate"] == 1.0
    assert summary["distribution"] == {1: 1, 2: 1}


def test_format_report_includes_rates_and_per_task_detail():
    results = [HitRateTaskResult("a", num_verified_candidates=1, top1_match=True, top2_match=True)]
    summary = summarize(results)
    report = format_report(results, summary)

    assert "Top-1 hit rate: 1.0000" in report
    assert "a: num_verified=1 top1=True top2=True" in report
