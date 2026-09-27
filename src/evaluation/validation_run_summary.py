"""Aggregate metrics for a validation-tier run of the consolidated config,
see docs/decisions/0034-first-validation-consolidated-config.md.

Pure post-processing over PerAttemptConditionalMitigationPairRow lists
(per_attempt_conditional_mitigation_pair_diagnostics.py), no GPU/model
dependency, same host-testable pattern as pair_diagnostics.py.

The close/middling/far bands are a new, explicit threshold introduced for
this ADR; ADR 0026 only described the pattern qualitatively (close:
0.73-0.90, middling: 0.45/0.59, far: 0.19 on its 8-task sample). 0.7 and
0.3 are chosen to match that precedent without over-fitting to those exact
numbers.
"""
from collections import defaultdict
from typing import Dict, List, Optional

from src.evaluation.per_attempt_conditional_mitigation_pair_diagnostics import (
    PerAttemptConditionalMitigationPairRow,
)

CLOSE_THRESHOLD = 0.7
FAR_THRESHOLD = 0.3

Row = PerAttemptConditionalMitigationPairRow


def _rows_for_split(rows: List[Row], split: str) -> List[Row]:
    return [r for r in rows if r.split == split]


def exact_match_rate(rows: List[Row], split: str = "test") -> float:
    split_rows = _rows_for_split(rows, split)
    if not split_rows:
        return 0.0
    return sum(1 for r in split_rows if r.constrained_exact_match) / len(split_rows)


def _band(accuracy: Optional[float]) -> str:
    if accuracy is None:
        return "far"
    if accuracy >= CLOSE_THRESHOLD:
        return "close"
    if accuracy < FAR_THRESHOLD:
        return "far"
    return "middling"


def per_cell_accuracy_distribution(rows: List[Row], split: str = "test") -> dict:
    """Mean (over rows with a measurable accuracy) plus close/middling/far
    counts (a missing accuracy, e.g. an unparseable or shape-mismatched
    prediction, counts as "far", per ADR 0026's precedent that a parse
    failure is at least as bad as a low content score)."""
    split_rows = _rows_for_split(rows, split)
    measurable = [r.constrained_best_cell_accuracy for r in split_rows if r.constrained_best_cell_accuracy is not None]
    counts = {"close": 0, "middling": 0, "far": 0}
    for r in split_rows:
        counts[_band(r.constrained_best_cell_accuracy)] += 1
    return {
        "n": len(split_rows),
        "mean": (sum(measurable) / len(measurable)) if measurable else None,
        **counts,
    }


def _rows_by_task(rows: List[Row]) -> Dict[str, List[Row]]:
    by_task = defaultdict(list)
    for r in rows:
        by_task[r.task_id].append(r)
    return by_task


def far_outlier_task_ids(rows: List[Row], threshold: float = FAR_THRESHOLD) -> List[str]:
    """Task ids showing the `13e47133` pattern from ADR 0026: clearly low
    content quality (or an unparseable/shape-mismatched prediction) even on
    the task's own train pairs, before generalization to held-out data is
    even in question."""
    far_tasks = []
    for task_id, task_rows in sorted(_rows_by_task(rows).items()):
        train_rows = _rows_for_split(task_rows, "train")
        accuracies = [r.constrained_best_cell_accuracy for r in train_rows]
        if accuracies and any(a is None or a < threshold for a in accuracies):
            far_tasks.append(task_id)
    return far_tasks


def project_time_for_task_count(measured_total_seconds: float, measured_task_count: int, target_task_count: int) -> float:
    if measured_task_count == 0:
        return 0.0
    per_task = measured_total_seconds / measured_task_count
    return per_task * target_task_count
