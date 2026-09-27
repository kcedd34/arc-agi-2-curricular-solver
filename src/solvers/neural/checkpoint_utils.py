"""Checkpoint discovery for resumable HF Trainer runs, see
docs/decisions/0036-piloto-pretreino-cross-task.md.

Per-task TTT stays checkpoint-free by default (a single task's training is
short, so the extra save I/O has nothing to buy); a long run (cross-task
pretraining, a future Kaggle notebook run) opts in via NeuralSolverConfig's
checkpoint_save_strategy and uses this module to find a checkpoint to
resume from after an interruption.
"""
import os
from typing import Optional

from transformers.trainer_utils import get_last_checkpoint


def find_resumable_checkpoint(output_dir: str) -> Optional[str]:
    """Returns the most recent checkpoint under output_dir, or None if the
    directory does not exist yet or holds no checkpoint (first run)."""
    if not os.path.isdir(output_dir):
        return None
    return get_last_checkpoint(output_dir)
