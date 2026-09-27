"""Attempt-loop with per-attempt conditional no_repeat_ngram_size escalation:
a refinement of conditional_generation_diagnostics.generate_with_conditional_counts
(ADR 0031), which only ever checked a pair's first attempt for ADR 0028's
degenerate pattern. ADR 0031 found this misses pairs whose first attempt is
an unrepresentative false negative: the pair then burns its entire attempt
budget under slow, unmitigated baseline decoding with no recovery
(0934a4d8 train pair 3, the case that made that task net slower than plain
baseline).

This version checks every attempt's own completion, not only the first, and
escalates as soon as any attempt so far shows the pattern - still short of
the global ngram_only config, which mitigates every attempt of every pair
unconditionally regardless of what any attempt looks like. Escalation is
one-way: once triggered for a pair, later attempts never fall back to the
baseline config.

Generic over an injected per-attempt completion function, same as ADR
0031's version, so this control flow is host-testable without a model/GPU.
See docs/decisions/0032-per-attempt-conditional-ngram-mitigation.md.

ADR 0056 measurement fix: shows_degenerate_pattern is now also used to
exclude a degenerate-but-parseable completion from predictions/num_kept
(still counted in num_parsed), not only to decide per-attempt escalation.

ADR 0058 circuit breaker wiring: accepts an optional TaskTimeLimiter,
checked once per attempt, mirroring generation.py's production
generate_grid_predictions loop. This diagnostic path had no per-task
time ceiling at all before this (ADR 0049 was never wired past
production code), a real integration gap closed here.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from src.evaluation.task_time_limit import TaskTimeLimiter
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
class PerAttemptConditionalGenerationDiagnostic:
    attempts_tried: int = 0
    num_parsed: int = 0
    num_parsed_but_degenerate: int = 0
    num_kept: int = 0
    escalated: bool = False
    escalated_at_attempt: Optional[int] = None
    predictions: List[Grid] = field(default_factory=list)
    raw_completions: List[str] = field(default_factory=list)


def generate_with_per_attempt_conditional_counts(
    generate_completion: CompletionFn,
    baseline_config: NeuralSolverConfig,
    enable_conditional_escalation: bool = True,
    escalated_no_repeat_ngram_size: int = DEFAULT_ESCALATED_NO_REPEAT_NGRAM_SIZE,
    limiter: Optional[TaskTimeLimiter] = None,
) -> PerAttemptConditionalGenerationDiagnostic:
    diag = PerAttemptConditionalGenerationDiagnostic()
    max_attempts = baseline_config.num_predictions * _MAX_SAMPLING_ATTEMPTS_PER_PREDICTION
    active_config = baseline_config
    for seed in range(max_attempts):
        if limiter is not None:
            limiter.check()
        if len(diag.predictions) >= baseline_config.num_predictions:
            break
        diag.attempts_tried += 1
        completion = generate_completion(active_config, seed)
        diag.raw_completions.append(completion)
        is_degenerate = shows_degenerate_pattern(completion)

        if not diag.escalated and enable_conditional_escalation and is_degenerate:
            diag.escalated = True
            diag.escalated_at_attempt = seed
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


__all__ = [
    "PerAttemptConditionalGenerationDiagnostic",
    "generate_with_per_attempt_conditional_counts",
]
