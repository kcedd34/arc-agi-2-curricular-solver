"""Diagnostic-only comparison of the chat-template prompt format against
prompt_builder.py's raw completion-style format, see
docs/decisions/0054-formato-chat-template-qwen3.md. Reuses ADR 0053's
sampling-loop instrumentation (generation_diagnostics.py) and ttt_trainer.py's
dataset/training-args helpers unchanged; only the text fed to the tokenizer
changes. Does not alter any production prompt-building or training code.

ADR 0056 measurement fix: excludes degenerate-but-parseable completions
(shows_degenerate_pattern) from predictions/num_kept while still counting
them in num_parsed, see generation_diagnostics.py's docstring for detail.
"""
from dataclasses import dataclass, field
from typing import List

import torch
from transformers import Trainer

from src.solvers.neural.chat_prompt_builder import build_chat_inference_prompt, build_chat_training_example
from src.solvers.neural.color_augmentation import expand_pairs_with_color_variants
from src.solvers.neural.conditional_mitigation import shows_degenerate_pattern
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.generation import _MAX_SAMPLING_ATTEMPTS_PER_PREDICTION, _generate_completion
from src.solvers.neural.grid_serialization import text_to_grid
from src.solvers.neural.prompt_builder import build_augmented_pairs
from src.solvers.neural.ttt_trainer import _TextDataset, _build_training_args
from src.utils.grid_ops import GEOMETRIC_TRANSFORMS, identity
from src.utils.grid_types import Grid
from src.utils.task_loader import Task


@dataclass
class ChatGenerationDiagnostic:
    attempts_tried: int = 0
    num_parsed: int = 0
    num_parsed_but_degenerate: int = 0
    num_kept: int = 0
    predictions: List[Grid] = field(default_factory=list)
    raw_completions: List[str] = field(default_factory=list)


def _build_chat_training_texts(task: Task, config: NeuralSolverConfig, tokenizer) -> List[str]:
    transforms = GEOMETRIC_TRANSFORMS if config.use_geometric_augmentation else [identity]
    pairs = build_augmented_pairs(task, transforms)
    if config.use_color_augmentation:
        pairs = expand_pairs_with_color_variants(
            pairs, config.num_color_augmentations_per_pair, config.color_augmentation_seed
        )
    return [build_chat_training_example(pair, tokenizer) for pair in pairs]


def train_on_task_chat(model, tokenizer, task: Task, config: NeuralSolverConfig):
    texts = _build_chat_training_texts(task, config, tokenizer)
    dataset = _TextDataset(texts, tokenizer, config.max_seq_length)
    trainer = Trainer(model=model, args=_build_training_args(config), train_dataset=dataset)
    torch.cuda.empty_cache()
    trainer.train()
    return model


def generate_with_counts_chat(model, tokenizer, grid_input: Grid, config: NeuralSolverConfig) -> ChatGenerationDiagnostic:
    prompt = build_chat_inference_prompt(grid_input, tokenizer)
    diag = ChatGenerationDiagnostic()
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
