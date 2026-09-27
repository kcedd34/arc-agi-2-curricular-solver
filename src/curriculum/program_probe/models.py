"""Local model handles for the probe (4-bit, HF offline). Requires the WSL2 GPU environment."""
import os
from typing import NamedTuple

MODEL_NAMES = {
    "base": "unsloth/qwen3-4b-base-unsloth-bnb-4bit",
    "instruct": "unsloth/qwen3-4b-instruct-2507-unsloth-bnb-4bit",
}
MAX_SEQ_LENGTH = 4096


class Loaded(NamedTuple):
    key: str
    model: object
    tokenizer: object


def load_model(key: str) -> Loaded:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAMES[key], max_seq_length=MAX_SEQ_LENGTH, load_in_4bit=True
    )
    FastLanguageModel.for_inference(model)
    return Loaded(key, model, tokenizer)
