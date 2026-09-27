"""Generates and decodes candidate grid predictions from the fine-tuned model."""
from typing import List, Optional

import torch
from transformers import StoppingCriteriaList

from src.evaluation.task_time_limit import TaskTimeLimiter
from src.solvers.neural.completion_markers import SECOND_EXAMPLE_MARKER as _SECOND_EXAMPLE_MARKER
from src.solvers.neural.conditional_mitigation import build_escalated_config, shows_degenerate_pattern
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.deadline_stopping_criteria import DeadlineStoppingCriteria
from src.solvers.neural.grid_serialization import text_to_grid
from src.solvers.neural.prompt_builder import build_inference_prompt
from src.utils.grid_types import Grid

_MAX_SAMPLING_ATTEMPTS_PER_PREDICTION = 3


def _truncate_before_second_input(text: str) -> str:
    marker_index = text.find(_SECOND_EXAMPLE_MARKER)
    if marker_index == -1:
        return text
    return text[:marker_index]


def _generate_completion(
    model,
    tokenizer,
    prompt: str,
    config: NeuralSolverConfig,
    seed: int,
    limiter: Optional[TaskTimeLimiter] = None,
) -> str:
    torch.manual_seed(seed)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    stopping_criteria = None
    if limiter is not None:
        # ADR 0049 circuit breaker: bounds a single generate() call so it
        # cannot by itself blow through the per-task ceiling, regardless of
        # max_new_tokens or how slow this particular completion turns out.
        stopping_criteria = StoppingCriteriaList([DeadlineStoppingCriteria(limiter.deadline())])
    output_ids = model.generate(
        **inputs,
        max_new_tokens=config.max_new_tokens,
        do_sample=True,
        temperature=config.generation_temperature,
        eos_token_id=tokenizer.eos_token_id,
        repetition_penalty=config.repetition_penalty,
        no_repeat_ngram_size=config.no_repeat_ngram_size,
        stopping_criteria=stopping_criteria,
    )
    full_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    completion = full_text[len(prompt):]
    if config.stop_on_second_input:
        completion = _truncate_before_second_input(completion)
    return completion


def generate_grid_predictions(
    model,
    tokenizer,
    test_input: Grid,
    config: NeuralSolverConfig,
    limiter: Optional[TaskTimeLimiter] = None,
) -> List[Grid]:
    """ADR 0032: every attempt is checked for the degenerate pattern (not
    only the first); on detection, this call's remaining attempts escalate
    one-way to no_repeat_ngram_size=3.

    ADR 0056: a completion that matches shows_degenerate_pattern (line-level
    repetition, a hallucinated second example, or topic drift) is never
    appended to predictions, even though it may still parse into a
    structurally valid grid, so a degenerate completion never reaches
    attempt_1/attempt_2 as a real submitted answer.

    limiter, when given, raises TaskTimeExceeded between attempts once the
    per-task neural time ceiling passes (ADR 0049 circuit breaker), on top
    of the mid-call stopping criteria _generate_completion already applies.
    """
    prompt = build_inference_prompt(test_input)
    predictions: List[Grid] = []
    max_attempts = config.num_predictions * _MAX_SAMPLING_ATTEMPTS_PER_PREDICTION
    active_config = config
    escalated = False
    for seed in range(max_attempts):
        if limiter is not None:
            limiter.check()
        if len(predictions) >= config.num_predictions:
            break
        completion = _generate_completion(model, tokenizer, prompt, active_config, seed, limiter)
        is_degenerate = shows_degenerate_pattern(completion)
        if not escalated and config.enable_conditional_escalation and is_degenerate:
            escalated = True
            active_config = build_escalated_config(config)
            print(
                f"[ADR0032] degenerate pattern detected at attempt {seed}, "
                f"escalating to no_repeat_ngram_size={active_config.no_repeat_ngram_size}"
            )
        grid = text_to_grid(completion)
        if grid is not None and not is_degenerate and grid not in predictions:
            predictions.append(grid)
    return predictions
