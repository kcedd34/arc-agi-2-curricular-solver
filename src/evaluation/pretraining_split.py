"""Task split for cross-task pretraining, disjoint from the sanity/
validation samples used to measure generalization. See
docs/decisions/0036-piloto-pretreino-cross-task.md.

Pretraining draws from the 1000-task public training split
(data/ARC-AGI-2/data/training/); every sanity/validation sample used so far
(ADR 0015/0017/0023/0026/0027/0034) was drawn from the disjoint 120-task
evaluation split (data/ARC-AGI-2/data/evaluation/), the default `split`
argument in every diagnostic runner script. Directory separation alone
already guarantees no overlap, but this module checks it at runtime rather
than trusting that convention silently.
"""
import json
import random
from pathlib import Path
from typing import Dict, List, Set

from src.utils.task_loader import Task

DEFAULT_PRETRAINING_SEED = 4242


def select_pretraining_tasks(
    training_tasks: Dict[str, Task], size: int, seed: int = DEFAULT_PRETRAINING_SEED
) -> Dict[str, Task]:
    """Deterministic sample of `size` tasks from the training split. Sorts
    ids before sampling so the result depends only on `size` and `seed`,
    never on dict iteration order."""
    sorted_ids = sorted(training_tasks)
    size = min(size, len(sorted_ids))
    chosen_ids = random.Random(seed).sample(sorted_ids, size)
    return {task_id: training_tasks[task_id] for task_id in sorted(chosen_ids)}


def assert_disjoint_from_reserved_tasks(pretraining_task_ids: Set[str], reserved_task_ids: Set[str]) -> None:
    overlap = pretraining_task_ids & reserved_task_ids
    if overlap:
        raise ValueError(f"Pretraining split overlaps with reserved evaluation tasks: {sorted(overlap)}")


def select_pretraining_tasks_excluding_reserved(
    training_tasks: Dict[str, Task],
    size: int,
    reserved_task_ids: Set[str],
    seed: int = DEFAULT_PRETRAINING_SEED,
) -> Dict[str, Task]:
    selected = select_pretraining_tasks(training_tasks, size, seed)
    assert_disjoint_from_reserved_tasks(set(selected), reserved_task_ids)
    return selected


def save_split_manifest(task_ids: List[str], path: Path) -> None:
    """Writes the exact chosen task ids to disk for audit/reproducibility,
    alongside the deterministic seed-based selection itself."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(task_ids), indent=2))
