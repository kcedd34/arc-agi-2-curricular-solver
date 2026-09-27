"""Rotating, seeded sample of the no-candidate pool for one round's Fase A
(continuous-loop.md Secao 3, Fase A.1): round n takes the n-th window of a
fixed deterministic shuffle, so consecutive rounds never see the same
sample and the whole pool is revisited on a fixed cadence.
"""
import hashlib
import json
from pathlib import Path
from typing import List, Optional

DEFAULT_POOL_PATH = Path("outputs/curriculum/no_candidate_pool.json")
SHUFFLE_SEED = "continuous-loop-diagnostics-v1"
DEFAULT_WINDOW_SIZE = 200


def load_pool(path: Path = DEFAULT_POOL_PATH) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def stable_shuffle(items: List[str], seed: str) -> List[str]:
    """Deterministic order, independent of Python's per-process hash
    randomization, so the same seed always yields the same permutation."""
    def sort_key(item: str) -> str:
        return hashlib.sha256(f"{seed}:{item}".encode("utf-8")).hexdigest()
    return sorted(items, key=sort_key)


def round_sample(
    round_number: int,
    window_size: int = DEFAULT_WINDOW_SIZE,
    pool: Optional[List[str]] = None,
    pool_path: Path = DEFAULT_POOL_PATH,
    seed: str = SHUFFLE_SEED,
) -> List[str]:
    items = pool if pool is not None else load_pool(pool_path)
    order = stable_shuffle(items, seed)
    n = len(order)
    if n == 0:
        return []
    start = ((round_number - 1) * window_size) % n
    indices = [(start + i) % n for i in range(min(window_size, n))]
    return [order[i] for i in indices]
