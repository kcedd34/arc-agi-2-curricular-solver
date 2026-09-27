"""Attempt-loop with conditional no_repeat_ngram_size escalation: the same
early-stop attempt budget as generation_diagnostics.generate_with_counts,
but only attempt 0 is guaranteed to use the caller's baseline config. If it
shows one of ADR 0028's two degenerate failure modes and escalation is
enabled, every remaining attempt for this pair switches to an escalated
no_repeat_ngram_size config (src.solvers.neural.conditional_mitigation)
instead of applying it to the whole run.

The loop is generic over an injected per-attempt completion function, so
its escalation control flow is host-testable without a model/GPU (a fake
completion function plugged in, real text_to_grid/failure-mode detection
underneath). See docs/decisions/0031-conditional-ngram-mitigation.md.

ADR 0056 measurement fix: shows_degenerate_pattern is now also used to
exclude a degenerate-but-parseable completion from predictions/num_kept
(still counted in num_parsed), not only to decide attempt-0 escalation.
"""
from dataclasses import dataclass, field
from typing import List

from src.solvers.neural.conditional_mitigation import (
    DEFAULT_ESCALATED_NO_REPEAT_NGRAM_SIZE,
    CompletionFn,
    build_escalated_config,
    shows_degenerate_pattern,
)
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.generation import _MAX_SAMPLING_ATTEMPTS_PER_PREDICTION
from src.solvers.neural.grid_serialization import text_to_grid
from src.utils.grid_types import Grid


@dataclass
class ConditionalGenerationDiagnostic:
    attempts_tried: int = 0
    num_parsed: int = 0
    num_parsed_but_degenerate: int = 0
    num_kept: int = 0
    escalated: bool = False
    predictions: List[Grid] = field(default_factory=list)
    raw_completions: List[str] = field(default_factory=list)


def generate_with_conditional_counts(
    generate_completion: CompletionFn,
    baseline_config: NeuralSolverConfig,
    enable_conditional_escalation: bool = True,
    escalated_no_repeat_ngram_size: int = DEFAULT_ESCALATED_NO_REPEAT_NGRAM_SIZE,
) -> ConditionalGenerationDiagnostic:
    diag = ConditionalGenerationDiagnostic()
    max_attempts = baseline_config.num_predictions * _MAX_SAMPLING_ATTEMPTS_PER_PREDICTION
    active_config = baseline_config
    for seed in range(max_attempts):
        if len(diag.predictions) >= baseline_config.num_predictions:
            break
        diag.attempts_tried += 1
        completion = generate_completion(active_config, seed)
        diag.raw_completions.append(completion)
        is_degenerate = shows_degenerate_pattern(completion)

        if seed == 0 and enable_conditional_escalation and is_degenerate:
            diag.escalated = True
            active_config = build_escalated_config(baseline_config, escalated_no_repeat_ngram_size)

        grid = text_to_grid(completion)
        if grid is not None:
            diag.num_parsed += 1
            if is_degenerate:
                diag.num_parsed_but_degenerate += 1
            elif grid not in diag.predictions:
                diag.predictions.append(grid)
    diag.num_kept = len(diag.predictions)
    return diag


__all__ = ["ConditionalGenerationDiagnostic", "generate_with_conditional_counts"]
