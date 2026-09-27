"""Adaptive decode-mitigation policy: decides, from a single raw completion,
whether the remaining generation attempts for that pair should escalate to
no_repeat_ngram_size mitigation, instead of applying it to every attempt of
every pair globally. ADR 0030 found the global version regresses held-out
accuracy on tasks that never show either failure mode by about 21%
relative; this policy tries to keep the fix only where the fix is needed.

Pure decision logic, no GPU/model dependency: reuses the same failure-mode
detectors ADR 0029/0030 used to measure the problem
(failure_mode_diagnostics.py), extended in
docs/decisions/0056-mitigacao-4-modos-qwen3-base.md with a third detector
(topic drift, observed on Qwen3-4B-Base) alongside the original two. See
docs/decisions/0031-conditional-ngram-mitigation.md.
"""
from dataclasses import replace
from typing import Callable

from src.evaluation.failure_mode_diagnostics import (
    has_degenerate_repetition,
    has_hallucinated_second_example,
    has_topic_drift,
)
from src.solvers.neural.config import NeuralSolverConfig

# Matches ADR 0030's ngram_only value, the config found to reproduce
# essentially all of the combined mitigation's failure-mode fix.
DEFAULT_ESCALATED_NO_REPEAT_NGRAM_SIZE = 3

# (config, seed) -> raw completion text. Mirrors generation._generate_completion's
# signature minus (model, tokenizer, prompt), so callers can inject a fake
# for host tests or a real model-backed closure for GPU runs.
CompletionFn = Callable[[NeuralSolverConfig, int], str]


def shows_degenerate_pattern(raw_completion: str) -> bool:
    """True if a single raw completion matches any failure mode this
    escalation policy watches for (ADR 0028: degenerate token repetition,
    or a hallucinated second Input:/Output: example; ADR 0056: topic drift
    into unrelated natural-language or code content, observed on
    Qwen3-4B-Base)."""
    return (
        has_hallucinated_second_example(raw_completion)
        or has_degenerate_repetition(raw_completion)
        or has_topic_drift(raw_completion)
    )


def build_escalated_config(
    baseline: NeuralSolverConfig,
    no_repeat_ngram_size: int = DEFAULT_ESCALATED_NO_REPEAT_NGRAM_SIZE,
) -> NeuralSolverConfig:
    """The config a pair's remaining attempts switch to once escalation
    triggers: no_repeat_ngram_size alone, matching ADR 0030's ngram_only
    config. repetition_penalty is left untouched, ADR 0030 found it close
    to inert on every axis measured (failure-mode fix, timing, and the
    regression alike)."""
    return replace(baseline, no_repeat_ngram_size=no_repeat_ngram_size)


__all__ = [
    "CompletionFn",
    "DEFAULT_ESCALATED_NO_REPEAT_NGRAM_SIZE",
    "shows_degenerate_pattern",
    "build_escalated_config",
]
