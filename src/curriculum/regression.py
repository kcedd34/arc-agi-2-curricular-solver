"""Re-verify previously solved tasks stay solved after a library change.

Run after adding or editing a src/curriculum/library/ primitive to
catch one that now shadows or breaks a task the curriculum already
counted as solved - the same "measure before declaring done" discipline
the prior solver line used (ADR 0043/0044/0045).
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List

from src.curriculum.verified_verdict import compute_verified_verdict

DEFAULT_TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


@dataclass
class RegressionResult:
    checked: List[str]
    regressed: List[str]


def run_regression(
    solved_task_ids: List[str], training_dir: Path = DEFAULT_TRAINING_DIR
) -> RegressionResult:
    """Re-verify every already-solved task id against the real gabarito
    (RN-CUR-04's two-attempt policy); `solved == False` is a regression.
    2026-09-22 correction: this used to flag a regression only when
    candidate unanimity broke, which would have silently accepted a task
    that stayed unanimous but became wrong against the gabarito."""
    regressed = []
    for task_id in solved_task_ids:
        verdict = compute_verified_verdict(task_id, training_dir)
        if not verdict.solved:
            regressed.append(task_id)
    return RegressionResult(checked=list(solved_task_ids), regressed=regressed)
