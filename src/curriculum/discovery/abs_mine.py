"""Mine contiguous subchains shared by two or more distinct solved tasks
(ADR 0110, Section 4). Matching uses token keys (kind, role, name); the
parameters stay free slots filled per use."""
from collections import defaultdict
from typing import Dict, List, NamedTuple, Set, Tuple

from src.curriculum.discovery.abs_tokens import THEN, Token

Key = Tuple[str, str, str]
MIN_LEN = 2
MIN_TASKS = 2


class Mined(NamedTuple):
    keys: Tuple[Key, ...]
    tasks: Tuple[str, ...]


def _windows(chain: Tuple[Token, ...]):
    keys = [t.key for t in chain]
    for start in range(len(keys)):
        for end in range(start + MIN_LEN, len(keys) + 1):
            window = tuple(keys[start:end])
            if window[0][1] != THEN and window[-1][1] != THEN:
                yield window


def support(chains: Dict[str, Tuple[Token, ...]]) -> Dict[Tuple[Key, ...], Set[str]]:
    seen: Dict[Tuple[Key, ...], Set[str]] = defaultdict(set)
    for task_id, chain in chains.items():
        for window in _windows(chain):
            seen[window].add(task_id)
    return {w: t for w, t in seen.items() if len(t) >= MIN_TASKS}


def _contains(longer: Tuple[Key, ...], shorter: Tuple[Key, ...]) -> bool:
    n = len(shorter)
    return any(longer[i : i + n] == shorter for i in range(len(longer) - n + 1))


def _dominated(window, tasks, shared) -> bool:
    """A subchain is redundant when a strictly longer shared chain has the same support."""
    return any(len(o) > len(window) and shared[o] == tasks and _contains(o, window) for o in shared)


def mine(chains: Dict[str, Tuple[Token, ...]]) -> List[Mined]:
    shared = support(chains)
    kept = [Mined(w, tuple(sorted(t))) for w, t in shared.items() if not _dominated(w, t, shared)]
    return sorted(kept, key=lambda m: (-len(m.tasks), -len(m.keys), m.keys))
