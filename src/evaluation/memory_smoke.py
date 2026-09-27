"""Measures peak VRAM usage across model load, TTT, and generation on a
single task, to validate the ~5GB Unsloth QLoRA estimate against this
project's actual worst-case task (per-task TTT, multi-demo prompts), see
the smoke-test-memory ADR. Requires a CUDA GPU, only runs inside the
project's WSL2 environment.
"""
from dataclasses import dataclass
from typing import Optional

import torch

from src.evaluation.generation_diagnostics import generate_with_counts
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.lora_setup import attach_fresh_lora, detach_lora
from src.solvers.neural.model_loader import load_base_model
from src.solvers.neural.ttt_trainer import train_on_task
from src.utils.task_loader import Task

MEMORY_STEPS = ("model_load", "ttt", "generation")


@dataclass
class MemorySmokeResult:
    task_id: str
    oom_step: Optional[str]
    peak_vram_bytes: int
    total_vram_bytes: int


def _total_vram_bytes() -> int:
    return torch.cuda.get_device_properties(0).total_memory


def _result(task_id: str, oom_step: Optional[str]) -> MemorySmokeResult:
    return MemorySmokeResult(task_id, oom_step, torch.cuda.max_memory_allocated(), _total_vram_bytes())


def run_memory_smoke_test(config: NeuralSolverConfig, task: Task) -> MemorySmokeResult:
    torch.cuda.reset_peak_memory_stats()
    try:
        base_model, tokenizer = load_base_model(config)
    except torch.cuda.OutOfMemoryError:
        return _result(task.task_id, "model_load")

    model = attach_fresh_lora(base_model, config)
    try:
        try:
            train_on_task(model, tokenizer, task, config)
        except torch.cuda.OutOfMemoryError:
            return _result(task.task_id, "ttt")

        try:
            for pair in [*task.train, *task.test]:
                generate_with_counts(model, tokenizer, pair.input, config)
        except torch.cuda.OutOfMemoryError:
            return _result(task.task_id, "generation")
    finally:
        detach_lora(model)

    return _result(task.task_id, None)
