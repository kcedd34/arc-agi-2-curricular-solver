"""Process-level discovery state (ADR 0110): the active utility registry that
orders the library, and a per-task trace of which properties were evaluated.
The registry is frozen while a batch runs, so every worker agrees on order."""
from typing import Optional, Set

from src.curriculum.discovery.registry import Registry

_registry: Optional[Registry] = None
_evaluated: Set[int] = set()
_effects = [0]


def set_registry(registry: Optional[Registry]) -> None:
    global _registry
    _registry = registry


def active_registry() -> Optional[Registry]:
    return _registry


def begin_trace() -> None:
    _evaluated.clear()
    _effects[0] = 0


def note_evaluated(indices) -> None:
    _evaluated.update(int(i) for i in indices)


def take_trace() -> Set[int]:
    taken = set(_evaluated)
    _evaluated.clear()
    return taken


def note_effects(count: int) -> None:
    _effects[0] = max(_effects[0], count)


def effects_tested() -> int:
    return _effects[0]
