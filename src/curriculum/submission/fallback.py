"""Empty-candidate safety net, mirroring ADR 0011 (kept independent of src/utils)."""
from collections import Counter
from typing import List, Optional

from src.curriculum.grid import Grid


def fallback_attempt_1(test_input: Grid) -> Grid:
    return test_input


def fallback_attempt_2(train_outputs: List[Grid], attempt_1: Grid) -> Grid:
    most_common = _unique_most_common(train_outputs)
    return most_common if most_common is not None else attempt_1


def _unique_most_common(grids: List[Grid]) -> Optional[Grid]:
    if not grids:
        return None
    by_key = {_key(g): g for g in grids}
    ranked = Counter(_key(g) for g in grids).most_common()
    top_key, top_count = ranked[0]
    if top_count <= 1 or (len(ranked) > 1 and ranked[1][1] == top_count):
        return None
    return by_key[top_key]


def _key(grid: Grid) -> tuple:
    return tuple(tuple(row) for row in grid)
