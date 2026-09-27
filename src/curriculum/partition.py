"""Deterministic curricular-pool / probe-pool partition, RN-CUR-05.

Splits the public ARC-AGI-2 training split (data/ARC-AGI-2/data/training/,
1000 tasks) into two disjoint sets:

- probe pool: a fixed-size (default 200), seeded random sample, held out
  from curricular development work and used only to measure
  generalization at defined checkpoints (PRD Section 14/UC-level probes).
- curricular pool: every remaining training task, freely used for
  curricular development (Stage 1 onward).

This is a different mechanism from the prior approach line's Golden
Rule 7 smoke/sanity/validation tiers (ADR 0015): those are diagnostic
sampling for that line's own solver, not a contamination-control
partition. RN-CUR-05 governs only this module.

`007bbfb7` is pinned to the curricular pool by explicit exclusion from
the probe-pool sample, since it is this project's own long-standing
Stage 1 smoke task and must never be held out from development.
"""
import json
import random
from pathlib import Path
from typing import Dict, List

DEFAULT_SEED = 20260921
DEFAULT_PROBE_POOL_SIZE = 200
PINNED_CURRICULAR_TASK_IDS = ["007bbfb7"]


def list_training_task_ids(training_dir: Path) -> List[str]:
    return sorted(p.stem for p in training_dir.glob("*.json"))


def partition_training_tasks(
    training_dir: Path,
    seed: int = DEFAULT_SEED,
    probe_pool_size: int = DEFAULT_PROBE_POOL_SIZE,
    pinned_curricular_task_ids: List[str] = None,
) -> Dict[str, object]:
    """Return a dict with seed, counts, and the two disjoint task-id lists.

    Deterministic: the same (training_dir contents, seed, probe_pool_size,
    pinned_curricular_task_ids) always produces the same partition.
    """
    pinned = list(pinned_curricular_task_ids or PINNED_CURRICULAR_TASK_IDS)
    all_ids = list_training_task_ids(training_dir)
    eligible_for_probe = sorted(set(all_ids) - set(pinned))

    rng = random.Random(seed)
    shuffled = eligible_for_probe[:]
    rng.shuffle(shuffled)
    probe_pool = sorted(shuffled[:probe_pool_size])
    curricular_pool = sorted(set(all_ids) - set(probe_pool))

    for task_id in pinned:
        if task_id in all_ids:
            assert task_id in curricular_pool
            assert task_id not in probe_pool

    return {
        "seed": seed,
        "probe_pool_size": len(probe_pool),
        "curricular_pool_size": len(curricular_pool),
        "total_training_tasks": len(all_ids),
        "pinned_curricular_task_ids": pinned,
        "probe_pool": probe_pool,
        "curricular_pool": curricular_pool,
    }


def write_partition(partition: Dict[str, object], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(partition, f, indent=2)
        f.write("\n")
