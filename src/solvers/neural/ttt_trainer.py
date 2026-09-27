"""Per-task test-time training: a short LoRA fine-tune using only the
task's own (augmented) training pairs, per ADR 0003.
"""
from typing import List, Optional

import torch
from torch.utils.data import Dataset
from transformers import Trainer, TrainingArguments

from src.evaluation.task_time_limit import TaskTimeLimiter
from src.solvers.neural.color_augmentation import expand_pairs_with_color_variants
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.deadline_callback import DeadlineTrainerCallback
from src.solvers.neural.prompt_builder import build_augmented_pairs, format_pair_as_text
from src.utils.grid_ops import GEOMETRIC_TRANSFORMS, identity
from src.utils.task_loader import Task


class _TextDataset(Dataset):
    def __init__(self, texts, tokenizer, max_seq_length):
        self.encodings = tokenizer(
            texts,
            truncation=True,
            max_length=max_seq_length,
            padding=True,
            return_tensors="pt",
        )

    def __len__(self):
        return self.encodings["input_ids"].shape[0]

    def __getitem__(self, idx):
        item = {key: tensor[idx] for key, tensor in self.encodings.items()}
        labels = item["input_ids"].clone()
        labels[item["attention_mask"] == 0] = -100
        item["labels"] = labels
        return item


def _build_training_args(config: NeuralSolverConfig) -> TrainingArguments:
    """save_strategy defaults to "no" (config.checkpoint_save_strategy's
    default), reproducing the exact prior no-checkpoint behavior for
    per-task TTT. A long run (cross-task pretraining, a future Kaggle
    notebook run) opts in via that same config field, see
    docs/decisions/0036-piloto-pretreino-cross-task.md.
    """
    return TrainingArguments(
        output_dir=config.checkpoint_output_dir,
        num_train_epochs=config.ttt_num_epochs,
        learning_rate=config.ttt_learning_rate,
        per_device_train_batch_size=2,
        logging_steps=1,
        save_strategy=config.checkpoint_save_strategy,
        save_steps=config.checkpoint_save_steps,
        save_total_limit=config.checkpoint_save_total_limit,
        report_to=[],
    )


def _texts_with_eos(texts: List[str], tokenizer) -> List[str]:
    """Appends the tokenizer's EOS token after each example's output grid, per
    ADR 0010: without it, training never shows the model where an output
    should end, so generation has no learned stop signal and runs to
    `max_new_tokens` almost every time regardless of the true grid size.
    """
    return [text + tokenizer.eos_token for text in texts]


def _build_training_texts(task: Task, config: NeuralSolverConfig) -> List[str]:
    """Geometric augmentation (ADR 0021), then color augmentation on top of
    it if enabled (ADR 0027), both only ever applied to train pairs."""
    transforms = GEOMETRIC_TRANSFORMS if config.use_geometric_augmentation else [identity]
    pairs = build_augmented_pairs(task, transforms)
    if config.use_color_augmentation:
        pairs = expand_pairs_with_color_variants(
            pairs, config.num_color_augmentations_per_pair, config.color_augmentation_seed
        )
    return [format_pair_as_text(pair) for pair in pairs]


def count_augmented_training_examples(task: Task, config: NeuralSolverConfig) -> int:
    """Number of augmented training texts train_on_task builds for this
    task, before EOS-appending/tokenization. Lets a caller compute
    s/example-epoch (docs/decisions/0057-dimensionamento-pretreino-v3-qwen3-base.md)
    without needing the HuggingFace Trainer's own internal step count,
    which train_on_task does not currently expose.
    """
    return len(_build_training_texts(task, config))


def train_on_task(
    model,
    tokenizer,
    task: Task,
    config: NeuralSolverConfig,
    resume_from_checkpoint: Optional[str] = None,
    limiter: Optional[TaskTimeLimiter] = None,
):
    """resume_from_checkpoint, when given, continues training from a saved
    checkpoint (see checkpoint_utils.find_resumable_checkpoint) instead of
    starting fresh. Only meaningful when config.checkpoint_save_strategy
    is not "no" for this run, see
    docs/decisions/0036-piloto-pretreino-cross-task.md.

    limiter, when given, aborts training with TaskTimeExceeded once the
    per-task neural time ceiling passes (ADR 0049 circuit breaker).
    """
    texts = _texts_with_eos(_build_training_texts(task, config), tokenizer)
    dataset = _TextDataset(texts, tokenizer, config.max_seq_length)
    callbacks = [DeadlineTrainerCallback(limiter)] if limiter is not None else None
    trainer = Trainer(model=model, args=_build_training_args(config), train_dataset=dataset, callbacks=callbacks)
    # Releases PyTorch's cached-but-unused reserved VRAM blocks before
    # training starts: on an 8GB card, unsloth's fused cross-entropy loss
    # reads torch.cuda.mem_get_info() to size itself and raises
    # ("No or negligible GPU memory available") if that reserved-but-idle
    # cache makes free memory look like zero, even though the model load
    # itself fits comfortably (observed 2026-09-14 pilot v2 run).
    torch.cuda.empty_cache()
    trainer.train(resume_from_checkpoint=resume_from_checkpoint)
    return model
