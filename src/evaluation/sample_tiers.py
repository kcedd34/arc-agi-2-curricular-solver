"""Layered task sampling for evaluation runs, see ADR 0015.

Three tiers, increasing cost and statistical weight:
- smoke: 1-2 tasks, fast mechanical check.
- sanity: 8 tasks, regression check before calling a change "ready".
- validation: 30-50 tasks, stratified by expected output grid size, the
  only tier allowed to back a policy/architecture ADR decision.
"""
import random
from typing import Dict, List, Optional

from src.utils.task_loader import Task

SMOKE_SIZE = 2
SANITY_SIZE = 8
VALIDATION_SIZE = 40
DEFAULT_SEED = 42

TIER_NAMES = ("smoke", "sanity", "validation")

_SMALL_MAX_CELLS = 100
_MEDIUM_MAX_CELLS = 400


def _task_output_size(task: Task) -> int:
    cells = [len(pair.output) * len(pair.output[0]) for pair in task.train + task.test if pair.output]
    return max(cells) if cells else 0


def _size_bin(cells: int) -> str:
    if cells <= _SMALL_MAX_CELLS:
        return "small"
    if cells <= _MEDIUM_MAX_CELLS:
        return "medium"
    return "large"


def _bin_task_ids(tasks: Dict[str, Task]) -> Dict[str, List[str]]:
    bins: Dict[str, List[str]] = {"small": [], "medium": [], "large": []}
    for task_id, task in tasks.items():
        bins[_size_bin(_task_output_size(task))].append(task_id)
    for ids in bins.values():
        ids.sort()
    return bins


def _counts_with_insufficient_slots(populated: Dict[str, int], target_total: int) -> Dict[str, int]:
    ranked = sorted(populated, key=lambda name: populated[name], reverse=True)
    chosen = set(ranked[:target_total])
    return {name: (1 if name in chosen else 0) for name in populated}


def _distribute_remainder(populated: Dict[str, int], remaining_target: int, total_available: int) -> Dict[str, int]:
    shares = {name: (populated[name] / total_available) * remaining_target for name in populated}
    capacity = {name: populated[name] - 1 for name in populated}
    extra = {name: min(int(shares[name]), capacity[name]) for name in populated}
    leftover = remaining_target - sum(extra.values())
    by_fraction = sorted(populated, key=lambda name: shares[name] - int(shares[name]), reverse=True)
    for name in by_fraction:
        if leftover <= 0:
            break
        if extra[name] < capacity[name]:
            extra[name] += 1
            leftover -= 1
    return extra


def _proportional_counts(bin_populations: Dict[str, int], target_total: int) -> Dict[str, int]:
    """Largest-remainder allocation with a 1-slot floor per non-empty bin, so
    a bin with a small population share is never silently dropped to zero.
    """
    populated = {name: pop for name, pop in bin_populations.items() if pop > 0}
    total_available = sum(populated.values())
    target_total = min(target_total, total_available)
    if target_total < len(populated):
        return _counts_with_insufficient_slots(populated, target_total)
    remaining_target = target_total - len(populated)
    extra = _distribute_remainder(populated, remaining_target, total_available)
    return {name: 1 + extra.get(name, 0) for name in populated}


def _stratified_sample(tasks: Dict[str, Task], target_total: int, seed: int) -> Dict[str, Task]:
    bins = _bin_task_ids(tasks)
    bin_populations = {name: len(ids) for name, ids in bins.items()}
    counts = _proportional_counts(bin_populations, target_total)
    rng = random.Random(seed)
    selected_ids: List[str] = []
    for name, ids in bins.items():
        selected_ids += rng.sample(ids, counts.get(name, 0))
    return {task_id: tasks[task_id] for task_id in sorted(selected_ids)}


def select_tier_tasks(
    tasks: Dict[str, Task],
    tier: str,
    seed: int = DEFAULT_SEED,
    size_override: Optional[int] = None,
) -> Dict[str, Task]:
    sorted_items = sorted(tasks.items())
    if tier == "smoke":
        return dict(sorted_items[: size_override or SMOKE_SIZE])
    if tier == "sanity":
        return dict(sorted_items[: size_override or SANITY_SIZE])
    if tier == "validation":
        target = size_override or VALIDATION_SIZE
        return _stratified_sample(dict(sorted_items), target, seed)
    raise ValueError(f"Unknown sampling tier: {tier!r}, expected 'smoke', 'sanity', or 'validation'")
