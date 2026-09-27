"""Iteration order for `ForEach.order` (ADR 0091)."""
from typing import Any, List, Optional

_KEYS = {
    "down": lambda r: -(r.row0 + r.rows - 1),
    "up": lambda r: r.row0,
    "right": lambda r: -(r.col0 + r.cols - 1),
    "left": lambda r: r.col0,
}


def ordered_items(items: List[Any], order: Optional[str]) -> List[Any]:
    """Items nearest to the `order` edge first (stable, so ties keep scan
    order). `None` keeps the list as is."""
    if order is None:
        return items
    if order not in _KEYS:
        raise ValueError(f"for_each: unknown order {order!r}")
    return sorted(items, key=_KEYS[order])
