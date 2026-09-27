"""Loads the base model via Unsloth (Qwen3-4B-Instruct-2507, per ADR 0051;
strategy per ADR 0003).

Requires a CUDA GPU and the unsloth/bitsandbytes/peft stack, this only
runs inside the project's native WSL2 environment (see
docs/decisions/0004-wsl2-native-execution.md).
"""
from typing import Tuple

from unsloth import FastLanguageModel

from src.solvers.neural.config import NeuralSolverConfig


def load_base_model(config: NeuralSolverConfig) -> Tuple[object, object]:
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config.model_name,
        max_seq_length=config.max_seq_length,
        load_in_4bit=config.load_in_4bit,
    )
    return model, tokenizer
