"""Named NeuralSolverConfig variants for the color-augmentation sanity
comparison: geometric augmentation alone (the current default) vs.
geometric augmentation plus a small number of additional color-permuted
variants per already-augmented train pair. See
docs/decisions/0027-color-augmentation-sanity.md.

num_color_augmentations_per_pair defaults to 2 (NeuralSolverConfig),
deliberately small for this first controlled test: color augmentation
multiplies on top of the already-active 8-transform D4 augmentation
(ADR 0021), so 2 extra color variants per geometric-augmented pair means
x3 the training volume on top of that 8x (24x the original pair count),
not another open-ended multiplier. Keeping the first count small bounds
the per-task TTT time increase (ADR 0013's budget) while this test
reads whether the effect is worth a larger count at all, rather than
combining "does it help" with "how much is enough" in one run.

Pure config construction, no GPU/model dependency, same pattern as
augmentation_configs.py/ablation_configs.py.
"""
from dataclasses import replace
from typing import List, Tuple

from src.solvers.neural.config import NeuralSolverConfig


def build_color_augmentation_configs() -> List[Tuple[str, NeuralSolverConfig]]:
    defaults = NeuralSolverConfig()
    geometric_only = replace(defaults, use_color_augmentation=False)
    geometric_plus_color = replace(defaults, use_color_augmentation=True)
    return [
        ("geometric_only", geometric_only),
        ("geometric_plus_color", geometric_plus_color),
    ]
