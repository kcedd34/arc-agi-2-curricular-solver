"""Samples raw program-induction completions from the model (ADR 0060).

Mirrors generation.py's structure (seed/tokenize/DeadlineStoppingCriteria/
model.generate/decode) but deliberately does not call
shows_degenerate_pattern or text_to_grid: those reject exactly the code
output this path wants (ADR 0060 blocker #1). Selection/verification of
the sampled completions happens in program_induction.py, not here.
"""
from typing import List, Optional

import torch
from transformers import StoppingCriteriaList

from src.evaluation.task_time_limit import TaskTimeLimiter
from src.solvers.neural.deadline_stopping_criteria import DeadlineStoppingCriteria
from src.solvers.neural.program_prompt_builder import build_induction_prompt
from src.utils.task_loader import Task

DEFAULT_NUM_CANDIDATES = 96
DEFAULT_MAX_NEW_TOKENS = 512
DEFAULT_TEMPERATURE = 0.7


def _sample_one(
    model,
    tokenizer,
    prompt: str,
    max_new_tokens: int,
    temperature: float,
    seed: int,
    limiter: Optional[TaskTimeLimiter],
) -> str:
    if limiter is not None:
        limiter.check()
    torch.manual_seed(seed)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    stopping_criteria = None
    if limiter is not None:
        stopping_criteria = StoppingCriteriaList([DeadlineStoppingCriteria(limiter.deadline())])
    output_ids = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=temperature,
        eos_token_id=tokenizer.eos_token_id,
        stopping_criteria=stopping_criteria,
    )
    full_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return full_text[len(prompt):]


def sample_program_completions(
    model,
    tokenizer,
    task: Task,
    num_candidates: int = DEFAULT_NUM_CANDIDATES,
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    limiter: Optional[TaskTimeLimiter] = None,
) -> List[str]:
    prompt = build_induction_prompt(task)
    return [
        _sample_one(model, tokenizer, prompt, max_new_tokens, temperature, seed, limiter)
        for seed in range(num_candidates)
    ]
