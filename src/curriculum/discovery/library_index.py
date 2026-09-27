"""Text -> library position of the generated properties, so a hypothesis that
names `gen:<expr>` can be credited to the registry entry that produced it."""
from functools import lru_cache
from typing import Dict, List

from src.curriculum.discovery.task_generated import _entries
from src.curriculum.spec._generated import PREFIX


@lru_cache(maxsize=1)
def _positions() -> Dict[str, int]:
    return {entry.text: index for index, entry in enumerate(_entries())}


def generated_texts(description: str) -> List[str]:
    """Every `gen:` expression named in a composition description."""
    texts, start = [], 0
    while True:
        at = description.find(PREFIX, start)
        if at < 0:
            return texts
        end = at + len(PREFIX)
        depth = 0
        while end < len(description):
            ch = description[end]
            depth += ch == "("
            depth -= ch == ")"
            if depth < 0 or (depth == 0 and ch in " ,]"):
                break
            end += 1
        texts.append(description[at + len(PREFIX) : end])
        start = end


def library_indices(description: str) -> List[int]:
    positions = _positions()
    return [positions[text] for text in generated_texts(description) if text in positions]
