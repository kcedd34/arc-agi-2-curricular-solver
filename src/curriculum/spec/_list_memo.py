"""Per-list memo of values derived from a whole region list (ADR 0090), e.g.
which region is the unique largest. Keyed by list identity with a strong
reference held, so a recycled id can never alias another list. Region lists
are never mutated in place after partition(), so a stored value stays valid.
"""
from typing import Any, Dict, List, Tuple

_MAX_ENTRIES = 512
_CACHE: Dict[int, Tuple[List[Any], Dict[str, Any]]] = {}


def list_memo(items: List[Any]) -> Dict[str, Any]:
    entry = _CACHE.get(id(items))
    if entry is None or entry[0] is not items:
        if len(_CACHE) >= _MAX_ENTRIES:
            _CACHE.clear()
        entry = (items, {})
        _CACHE[id(items)] = entry
    return entry[1]
