"""Per-task prediction: verified candidates -> up to two distinct attempts."""
from typing import List

from src.curriculum.grid import Grid
from src.curriculum.loader import Task


def solve_task_attempts(task: Task) -> List[List[Grid]]:
    """Up to two attempts; each attempt holds one grid per test input.

    Same pipeline as `verified_verdict.compute_verified_verdict`, without
    any gabarito access (none exists for a real test set).
    """
    from src.curriculum.search.all_candidates import all_verified_pairs
    from src.curriculum.search.candidate_rank import rank_by_simplicity
    from src.curriculum.verified_verdict import distinct_attempts

    ranked = rank_by_simplicity(all_verified_pairs(task).combined())
    return distinct_attempts(ranked)
