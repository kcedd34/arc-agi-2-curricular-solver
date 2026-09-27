"""Chat-template prompt building for Qwen3-Instruct's official chat interface.

Alternative to prompt_builder.py's raw completion-style format. See
docs/decisions/0054-formato-chat-template-qwen3.md for the smoke test
comparing the two against ADR 0053's Qwen3-Instruct-specific failure modes.
"""
from src.solvers.neural.grid_serialization import grid_to_text
from src.utils.grid_types import Grid
from src.utils.task_loader import Pair

CHAT_SYSTEM_PROMPT = (
    "You solve grid transformation puzzles. Respond with only the output "
    "grid as rows of space-free digits, one row per line. Do not include "
    "any explanation, reasoning, or text of any kind besides the grid."
)


def _user_message(grid_input: Grid) -> str:
    return f"Input:\n{grid_to_text(grid_input)}"


def build_chat_training_example(pair: Pair, tokenizer) -> str:
    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "user", "content": _user_message(pair.input)},
        {"role": "assistant", "content": grid_to_text(pair.output)},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)


def build_chat_inference_prompt(grid_input: Grid, tokenizer) -> str:
    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "user", "content": _user_message(grid_input)},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
