"""Task ids already spent by the sanity/validation samples (ADR 0015),
reserved so the cross-task pretraining split (ADR 0036) never selects them.
See pretraining_split.py, which enforces this as a runtime check rather
than trusting the two data directories stay separate by convention alone.
"""
from pathlib import Path
from typing import Set

from src.evaluation.sample_tiers import select_tier_tasks
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVALUATION_DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data" / "evaluation"


def reserved_evaluation_task_ids(seed: int = 42) -> Set[str]:
    """Union of the exact task ids selected by the sanity tier (ADR 0017/
    0023/0026/0027, first 8 tasks sorted by id, no seed) and the validation
    tier (ADR 0034, stratified sample, seed=42 by default), both drawn from
    the 120-task evaluation split. The two tiers are not themselves disjoint
    (the validation tier samples from the full evaluation pool without
    excluding the sanity 8), so this is a union, not a sum: 44 unique tasks
    at the default seed, not 48.
    """
    evaluation_tasks = load_task_set(EVALUATION_DATA_ROOT)
    sanity_ids = set(select_tier_tasks(evaluation_tasks, "sanity").keys())
    validation_ids = set(select_tier_tasks(evaluation_tasks, "validation", seed=seed).keys())
    return sanity_ids | validation_ids
