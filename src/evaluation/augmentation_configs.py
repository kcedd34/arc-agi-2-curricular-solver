"""Named NeuralSolverConfig variants for the ADR 0021 geometric augmentation
smoke test: a genuine no-augmentation control vs. the full 8-transform D4
augmentation, on the same 2 tasks ADR 0018/0019 used. See
docs/decisions/0021-augmentation-geometric-smoke-test.md.

Pure config construction, no GPU/model dependency, kept in its own file so
it stays host-testable (same pattern as ablation_configs.py).
"""
from dataclasses import replace
from typing import List, Tuple

from src.solvers.neural.config import NeuralSolverConfig


def build_augmentation_configs() -> List[Tuple[str, NeuralSolverConfig]]:
    defaults = NeuralSolverConfig()
    no_augmentation = replace(defaults, use_geometric_augmentation=False)
    geometric_full = replace(defaults, use_geometric_augmentation=True)
    return [
        ("no_augmentation", no_augmentation),
        ("geometric_full", geometric_full),
    ]
