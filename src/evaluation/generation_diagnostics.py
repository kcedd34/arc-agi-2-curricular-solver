"""Instrumented mirror of src/solvers/neural/generation.py's sampling loop.

Reports raw counts (attempts tried, how many decoded to a valid grid, how
many survived after dedup) instead of only the final kept predictions.
Diagnostic only: does not change generation behavior, just observes it.
See docs/decisions/0009-empty-candidate-diagnosis.md.

ADR 0056 measurement fix: a completion can be structurally parseable (all
non-blank lines all-digit and of consistent width) while its content is
degenerate repetition, not a genuine prediction (ADR 0053/0055 found this
inflates num_parsed/num_kept, e.g. 136b0064's all-zero repeated grid).
Completions matching shows_degenerate_pattern are still counted toward
num_parsed (they did parse) but excluded from predictions/num_kept.
"""
from dataclasses import dataclass, field
from typing import List

from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.conditional_mitigation import shows_degenerate_pattern
from src.solvers.neural.generation import _MAX_SAMPLING_ATTEMPTS_PER_PREDICTION, _generate_completion
from src.solvers.neural.grid_serialization import text_to_grid
from src.solvers.neural.prompt_builder import build_inference_prompt
from src.utils.grid_types import Grid


@dataclass
class GenerationDiagnostic:
    attempts_tried: int = 0
    num_parsed: int = 0
    num_parsed_but_degenerate: int = 0
    num_kept: int = 0
    predictions: List[Grid] = field(default_factory=list)
    raw_completions: List[str] = field(default_factory=list)


def generate_with_counts(model, tokenizer, grid_input: Grid, config: NeuralSolverConfig) -> GenerationDiagnostic:
    prompt = build_inference_prompt(grid_input)
    diag = GenerationDiagnostic()
    max_attempts = config.num_predictions * _MAX_SAMPLING_ATTEMPTS_PER_PREDICTION
    for seed in range(max_attempts):
        if len(diag.predictions) >= config.num_predictions:
            break
        diag.attempts_tried += 1
        completion = _generate_completion(model, tokenizer, prompt, config, seed)
        diag.raw_completions.append(completion)
        grid = text_to_grid(completion)
        if grid is not None:
            diag.num_parsed += 1
            if shows_degenerate_pattern(completion):
                diag.num_parsed_but_degenerate += 1
            elif grid not in diag.predictions:
                diag.predictions.append(grid)
    diag.num_kept = len(diag.predictions)
    return diag
