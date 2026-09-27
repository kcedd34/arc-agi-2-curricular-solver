"""Empty-candidate safety net for the final submission layer, per ADR 0011.

Applied only when a solver returns zero candidate grids for a test pair.
Does not alter neural or symbolic solver behavior.
"""
from collections import Counter
from typing import List, Optional, Tuple

from src.utils.grid_types import Grid
from src.utils.task_loader import Pair


def fallback_attempt_1(test_pair: Pair) -> Grid:
    return test_pair.input


def fallback_attempt_2(train: List[Pair], attempt_1: Grid) -> Grid:
    most_common = _most_common_train_output(train)
    return most_common if most_common is not None else attempt_1


def _most_common_train_output(train: List[Pair]) -> Optional[Grid]:
    if not train:
        return None
    output_by_key = {_grid_key(pair.output): pair.output for pair in train}
    counts = Counter(_grid_key(pair.output) for pair in train)
    ranked = counts.most_common()
    top_key, top_count = ranked[0]
    if top_count <= 1:
        return None
    if len(ranked) > 1 and ranked[1][1] == top_count:
        return None
    return output_by_key[top_key]


def _grid_key(grid: Grid) -> Tuple[Tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)
