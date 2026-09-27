"""Cell-level category of a task (misto, muda a forma, desenha, recolore, move, apaga)."""
from collections import Counter
from typing import List, Sequence, Tuple

Pair = Tuple[list, list]
SHAPE, DRAW, RECOLOR, MOVE, ERASE, MIXED = "muda a forma", "desenha", "recolore", "move", "apaga", "misto"


def _shape(grid: Sequence[Sequence[int]]) -> Tuple[int, int]:
    return len(grid), len(grid[0])


def _changes(source: list, target: list) -> List[Tuple[int, int]]:
    return [(a, b) for ra, rb in zip(source, target) for a, b in zip(ra, rb) if a != b]


def _same_colours(source: list, target: list) -> bool:
    count = lambda g: Counter(v for row in g for v in row if v)
    return count(source) == count(target)


def _pair_kind(source: list, target: list) -> str:
    if _shape(source) != _shape(target):
        return SHAPE
    changes = _changes(source, target)
    if not changes:
        return "same"
    if all(a == 0 for a, _ in changes):
        return DRAW
    if all(b == 0 for _, b in changes):
        return ERASE
    if all(a != 0 and b != 0 for a, b in changes):
        return RECOLOR
    return MOVE if _same_colours(source, target) else MIXED


def task_category(pairs: Sequence[Pair]) -> str:
    kinds = {_pair_kind(a, b) for a, b in pairs} - {"same"}
    if len(kinds) == 1:
        return kinds.pop()
    return SHAPE if SHAPE in kinds else MIXED
