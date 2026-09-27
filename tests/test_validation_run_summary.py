from src.evaluation.per_attempt_conditional_mitigation_pair_diagnostics import (
    PerAttemptConditionalMitigationPairRow,
)
from src.evaluation.validation_run_summary import (
    exact_match_rate,
    far_outlier_task_ids,
    per_cell_accuracy_distribution,
    project_time_for_task_count,
)


def _row(task_id, split, accuracy, exact_match=False):
    return PerAttemptConditionalMitigationPairRow(
        config_name="consolidated_current",
        task_id=task_id,
        split=split,
        pair_index=0,
        attempts_tried=1,
        num_kept=1,
        num_hallucinated=0,
        num_repetitive=0,
        escalated=False,
        escalated_at_attempt=None,
        constrained_exact_match=exact_match,
        constrained_best_cell_accuracy=accuracy,
    )


def test_exact_match_rate_only_counts_requested_split():
    rows = [
        _row("t1", "train", 1.0, exact_match=True),
        _row("t1", "test", 0.9, exact_match=True),
        _row("t2", "test", 0.5, exact_match=False),
    ]
    assert exact_match_rate(rows, split="test") == 0.5


def test_exact_match_rate_empty_split_returns_zero():
    rows = [_row("t1", "train", 1.0, exact_match=True)]
    assert exact_match_rate(rows, split="test") == 0.0


def test_per_cell_accuracy_distribution_bands_and_mean():
    rows = [
        _row("t1", "test", 0.9),
        _row("t2", "test", 0.5),
        _row("t3", "test", 0.1),
        _row("t4", "test", None),
    ]
    dist = per_cell_accuracy_distribution(rows, split="test")
    assert dist["n"] == 4
    assert dist["close"] == 1
    assert dist["middling"] == 1
    assert dist["far"] == 2
    assert dist["mean"] == (0.9 + 0.5 + 0.1) / 3


def test_per_cell_accuracy_distribution_no_measurable_rows_has_none_mean():
    rows = [_row("t1", "test", None)]
    dist = per_cell_accuracy_distribution(rows, split="test")
    assert dist["mean"] is None
    assert dist["far"] == 1


def test_far_outlier_task_ids_flags_low_train_accuracy():
    rows = [
        _row("t1", "train", 0.9),
        _row("t1", "train", 0.85),
        _row("t2", "train", 0.1),
        _row("t2", "train", 0.9),
    ]
    assert far_outlier_task_ids(rows) == ["t2"]


def test_far_outlier_task_ids_flags_unparseable_train_prediction():
    rows = [_row("t1", "train", None)]
    assert far_outlier_task_ids(rows) == ["t1"]


def test_far_outlier_task_ids_ignores_tasks_with_no_train_rows():
    rows = [_row("t1", "test", 0.1)]
    assert far_outlier_task_ids(rows) == []


def test_project_time_for_task_count_scales_linearly():
    assert project_time_for_task_count(800.0, 8, 40) == 4000.0


def test_project_time_for_task_count_zero_measured_tasks_is_zero():
    assert project_time_for_task_count(800.0, 0, 40) == 0.0
