"""Builds TTT training examples and inference prompts for the neural solver.

Training pairs are augmented with geometric transforms (src/utils/grid_ops.py)
applied consistently to both sides of each pair, following the same
D4-symmetry augmentation used by prior ARC-AGI-2 solutions (see ADR 0003
references). Which transforms to apply is the caller's choice, see
docs/decisions/0021-augmentation-geometric-smoke-test.md: pass
GEOMETRIC_TRANSFORMS (the default) for the full D4 set, or [identity] for a
genuine no-augmentation control.
"""
from typing import List

from src.utils.grid_ops import GEOMETRIC_TRANSFORMS, Transform
from src.utils.grid_types import Grid
from src.utils.task_loader import Pair, Task
from src.solvers.neural.grid_serialization import grid_to_text

PROMPT_PREFIX = "Input:\n"
COMPLETION_PREFIX = "\nOutput:\n"


def format_pair_as_text(pair: Pair) -> str:
    return f"{PROMPT_PREFIX}{grid_to_text(pair.input)}{COMPLETION_PREFIX}{grid_to_text(pair.output)}"


def build_inference_prompt(test_input: Grid) -> str:
    return f"{PROMPT_PREFIX}{grid_to_text(test_input)}{COMPLETION_PREFIX}"


def _augment_pair(pair: Pair, transforms: List[Transform]) -> List[Pair]:
    return [Pair(transform(pair.input), transform(pair.output)) for transform in transforms]


def build_augmented_pairs(task: Task, transforms: List[Transform] = GEOMETRIC_TRANSFORMS) -> List[Pair]:
    """The task's train pairs after geometric augmentation, as Pair objects
    (not yet formatted to text), so a caller can expand them further (e.g.
    color_augmentation.py) before formatting. See ttt_trainer.py."""
    pairs: List[Pair] = []
    for pair in task.train:
        pairs += _augment_pair(pair, transforms)
    return pairs


def build_training_examples(task: Task, transforms: List[Transform] = GEOMETRIC_TRANSFORMS) -> List[str]:
    return [format_pair_as_text(pair) for pair in build_augmented_pairs(task, transforms)]
