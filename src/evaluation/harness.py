"""Local evaluation harness against the public ARC-AGI-2 dataset."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from src.evaluation.metrics import scores_test_pair
from src.evaluation.prediction_store import save_predictions
from src.evaluation.sample_tiers import select_tier_tasks
from src.utils.task_loader import Task, load_task_set

Solver = Callable[[Task], List[List]]


@dataclass
class EvalResult:
    total_test_pairs: int = 0
    correct_test_pairs: int = 0
    per_task_correct: Dict[str, int] = field(default_factory=dict)
    per_task_total: Dict[str, int] = field(default_factory=dict)

    @property
    def accuracy(self) -> float:
        if self.total_test_pairs == 0:
            return 0.0
        return self.correct_test_pairs / self.total_test_pairs


def evaluate_solver(
    solver: Solver, tasks: Dict[str, Task], predictions_dir: Optional[Path] = None
) -> EvalResult:
    result = EvalResult()
    for task_id, task in tasks.items():
        predictions_per_pair = solver(task)
        if predictions_dir is not None:
            save_predictions(task_id, predictions_per_pair, predictions_dir)
        result.per_task_total[task_id] = len(task.test)
        result.per_task_correct[task_id] = 0
        for predictions, pair in zip(predictions_per_pair, task.test):
            result.total_test_pairs += 1
            if scores_test_pair(predictions, pair.output):
                result.correct_test_pairs += 1
                result.per_task_correct[task_id] += 1
    return result


def evaluate_solver_on_directory(
    solver: Solver,
    data_dir: Path,
    limit: int = None,
    predictions_dir: Optional[Path] = None,
    tier: Optional[str] = None,
) -> EvalResult:
    """`limit` takes a raw first-N slice; `tier` (see ADR 0015, one of
    "smoke"/"sanity"/"validation") takes the layer-appropriate sample instead.
    `limit` wins if both are given. Neither given returns the full split.
    """
    tasks = load_task_set(data_dir)
    if limit is not None:
        tasks = dict(list(tasks.items())[:limit])
    elif tier is not None:
        tasks = select_tier_tasks(tasks, tier)
    return evaluate_solver(solver, tasks, predictions_dir=predictions_dir)
