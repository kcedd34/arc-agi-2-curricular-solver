"""Text generation for the probe: N sampled completions of one prompt, with timing."""
import time
from typing import List, NamedTuple

from src.curriculum.program_probe.models import Loaded
from src.curriculum.program_probe.decoding import comment_token_ids
from src.curriculum.program_probe.prompt import Prompt, base_response_head, chat_messages

MAX_NEW_TOKENS = 800
TEMPERATURE = 0.7
BATCH = 5
STOP = ["```"]


class Batch(NamedTuple):
    texts: List[str]
    seconds: float
    new_tokens: int


def encode(loaded: Loaded, prompt: Prompt):
    tokenizer = loaded.tokenizer
    if loaded.key == "instruct":
        text = tokenizer.apply_chat_template(chat_messages(prompt), tokenize=False, add_generation_prompt=True)
        text += base_response_head(prompt.variant)
    else:
        text = prompt.base_text
    return tokenizer(text, return_tensors="pt", add_special_tokens=False).to("cuda")


def _generate_kwargs(loaded: Loaded, count: int, temperature: float) -> dict:
    kwargs = {"max_new_tokens": MAX_NEW_TOKENS, "num_return_sequences": count, "pad_token_id": loaded.tokenizer.pad_token_id,
              "bad_words_ids": comment_token_ids(loaded.tokenizer)}
    if temperature > 0:
        kwargs.update(do_sample=True, temperature=temperature, top_p=0.95)
    else:
        kwargs.update(do_sample=False)
    kwargs.update(stop_strings=STOP, tokenizer=loaded.tokenizer)
    return kwargs


def generate(loaded: Loaded, prompt: Prompt, count: int, temperature: float) -> Batch:
    import torch

    inputs = encode(loaded, prompt)
    start = time.time()
    with torch.no_grad():
        out = loaded.model.generate(**inputs, **_generate_kwargs(loaded, count, temperature))
    seconds = time.time() - start
    new = out[:, inputs["input_ids"].shape[1]:]
    texts = loaded.tokenizer.batch_decode(new, skip_special_tokens=True)
    tokens = int((new != loaded.tokenizer.pad_token_id).sum())
    return Batch(texts, seconds, tokens)


def prompt_tokens(loaded: Loaded, prompt: Prompt) -> int:
    return int(encode(loaded, prompt)["input_ids"].shape[1])
