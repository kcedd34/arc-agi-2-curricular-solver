"""Cross-task pretraining: one shared LoRA adapter trained across many
tasks' augmented examples before per-task TTT, testing ADR 0022's
hypothesis. See docs/decisions/0036-piloto-pretreino-cross-task.md.

Task-boundary handling is intentionally simple for this first pilot: every
selected task's augmented training texts (same geometric + color
augmentation used for per-task TTT, ttt_trainer.build_training_texts) are
pooled into one corpus and shuffled once up front, with no per-task
curriculum, weighting, or boundary marker. This is a named simplification
for a first signal, not a claim that it is the best design.
"""
import random
from typing import Dict, List, Optional

import torch
from transformers import Trainer

from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.ttt_trainer import (
    _TextDataset,
    _build_training_args,
    _build_training_texts,
    _texts_with_eos,
)
from src.utils.task_loader import Task


def build_cross_task_corpus(tasks: Dict[str, Task], config: NeuralSolverConfig, seed: int = 42) -> List[str]:
    """Pools every selected task's augmented training texts (same
    geometric + color augmentation as per-task TTT) into one shuffled
    corpus, so no task's examples all land in the same training batch."""
    texts: List[str] = []
    for task in tasks.values():
        texts += _build_training_texts(task, config)
    random.Random(seed).shuffle(texts)
    return texts


def pretrain_shared_adapter(
    model,
    tokenizer,
    tasks: Dict[str, Task],
    config: NeuralSolverConfig,
    resume_from_checkpoint: Optional[str] = None,
):
    """Trains one shared LoRA adapter (already attached to `model`, e.g.
    via lora_setup.attach_fresh_lora) across every selected task's pooled
    corpus. Returns the trained model; call model.save_pretrained(dir) to
    persist the resulting adapter for a later per-task warm start
    (lora_setup.attach_pretrained_lora). Reuses ttt_trainer's private
    corpus/dataset/args builders directly (same convention already used by
    tests/test_ttt_trainer.py) rather than duplicating them.
    """
    epochs_config = _pretraining_epochs_config(config)
    texts = _texts_with_eos(build_cross_task_corpus(tasks, config), tokenizer)
    dataset = _TextDataset(texts, tokenizer, config.max_seq_length)
    trainer = Trainer(model=model, args=_build_training_args(epochs_config), train_dataset=dataset)
    # See the matching comment in ttt_trainer.train_on_task: releases
    # PyTorch's cached-but-unused reserved VRAM so unsloth's fused
    # cross-entropy loss does not mistake it for zero free memory.
    torch.cuda.empty_cache()
    trainer.train(resume_from_checkpoint=resume_from_checkpoint)
    return model


def _pretraining_epochs_config(config: NeuralSolverConfig) -> NeuralSolverConfig:
    """_build_training_args reads num_train_epochs from ttt_num_epochs;
    this swaps in pretraining_num_epochs for just this call, without
    mutating the caller's config or duplicating _build_training_args."""
    import dataclasses

    return dataclasses.replace(config, ttt_num_epochs=config.pretraining_num_epochs)
