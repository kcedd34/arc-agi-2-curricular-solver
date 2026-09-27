"""Direction and distance toward a target region (ADR 0098, second case).

A region is aligned with a target when their row spans (or column spans)
overlap and the boxes do not; the direction is then the axis-aligned one
toward the target and the distance is the number of empty steps before
the boxes touch. With several targets the nearest aligned one wins.
"""
from typing import Any, List, Optional, Tuple

from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._region_value import RegionValue

Toward = Tuple[Tuple[int, int], int]


def _overlap(a0: int, a1: int, b0: int, b1: int) -> bool:
    return a0 <= b1 and b0 <= a1


def _toward_one(base: RegionValue, target: RegionValue) -> Optional[Toward]:
    b_r1, b_c1 = base.row0 + base.rows - 1, base.col0 + base.cols - 1
    t_r1, t_c1 = target.row0 + target.rows - 1, target.col0 + target.cols - 1
    if _overlap(base.row0, b_r1, target.row0, t_r1):
        if b_c1 < target.col0:
            return (0, 1), target.col0 - b_c1 - 1
        if t_c1 < base.col0:
            return (0, -1), base.col0 - t_c1 - 1
    if _overlap(base.col0, b_c1, target.col0, t_c1):
        if b_r1 < target.row0:
            return (1, 0), target.row0 - b_r1 - 1
        if t_r1 < base.row0:
            return (-1, 0), base.row0 - t_r1 - 1
    return None


def _as_targets(target: Any) -> List[RegionValue]:
    items = target if isinstance(target, list) else [target]
    if not items or not all(isinstance(t, RegionValue) for t in items):
        raise InterpreterError("toward: target must be a region or a non-empty region list")
    return items


def toward_target(base: RegionValue, target: Any) -> Toward:
    options = [hit for hit in (_toward_one(base, t) for t in _as_targets(target)) if hit]
    if not options:
        raise InterpreterError("toward: region is not aligned with any target")
    return min(options, key=lambda hit: hit[1])
