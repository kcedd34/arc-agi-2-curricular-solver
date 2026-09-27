"""Decoding constraint: forbid comment tokens, so the model cannot spend its budget reasoning in comments."""
from typing import List

_CACHE: dict = {}


def comment_token_ids(tokenizer) -> List[List[int]]:
    """Ids of every vocabulary token whose text contains `#`, as single-token bad-word entries."""
    key = id(tokenizer)
    if key not in _CACHE:
        ids = [i for i in range(len(tokenizer)) if "#" in tokenizer.decode([i])]
        _CACHE[key] = [[i] for i in ids]
    return _CACHE[key]
