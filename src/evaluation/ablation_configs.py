"""Named NeuralSolverConfig variants for the ADR 0018 follow-up ablation
(more TTT epochs vs. larger LoRA rank), distinguishing under-training from
insufficient per-task demonstration signal. See
docs/decisions/0019-hyperparameter-ablation-input-copying.md.

Pure config construction, no GPU/model dependency, kept in its own file so
it stays host-testable (same pattern as task_selector.py).
"""
from dataclasses import replace
from typing import List, Tuple

from src.solvers.neural.config import NeuralSolverConfig


def build_ablation_configs() -> List[Tuple[str, NeuralSolverConfig]]:
    baseline = NeuralSolverConfig()
    more_epochs = replace(baseline, ttt_num_epochs=baseline.ttt_num_epochs * 2)
    larger_rank = replace(
        baseline,
        lora_rank=baseline.lora_rank * 2,
        lora_alpha=baseline.lora_alpha * 2,
    )
    return [
        ("baseline", baseline),
        ("epochs_x2", more_epochs),
        ("lora_rank_x2", larger_rank),
    ]
