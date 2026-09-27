"""Builds the per-pair error diagnostic report for a solver run.

One row per test pair: dimension match, per-cell accuracy (only when
dimensions match), and a coarse error-type classification derived from
the task's own train pairs (see error_classifier.py).
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from src.evaluation.error_classifier import classify_task_transform
from src.evaluation.harness import Solver
from src.evaluation.pair_diagnostics import best_pair_diagnostic
from src.evaluation.prediction_store import save_predictions
from src.utils.task_loader import Task


@dataclass
class PairReport:
    task_id: str
    pair_index: int
    dimension_match: bool
    per_cell_accuracy: Optional[float]
    error_class: str


def build_error_report(
    solver: Solver, tasks: Dict[str, Task], predictions_dir: Optional[Path] = None
) -> List[PairReport]:
    reports = []
    for task_id, task in tasks.items():
        predictions_per_pair = solver(task)
        if predictions_dir is not None:
            save_predictions(task_id, predictions_per_pair, predictions_dir)
        error_class = classify_task_transform(task)
        for pair_index, (predictions, pair) in enumerate(zip(predictions_per_pair, task.test)):
            dim_match, accuracy = best_pair_diagnostic(predictions, pair.output)
            reports.append(PairReport(task_id, pair_index, dim_match, accuracy, error_class))
    return reports
