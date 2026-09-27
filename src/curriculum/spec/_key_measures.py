"""Key-cell measures (ADR 0109): a stamp template carries one cell whose
colour appears nowhere else in it; that cell says where the template is
pinned to an anchor. Ambiguous regions have no key (colour -1, offset 0)."""
from collections import Counter
from typing import Any, Optional, Tuple

from src.curriculum.spec._region_value import RegionValue

NO_KEY = -1


def _key_position(region: RegionValue) -> Optional[Tuple[int, int, int]]:
    counts = Counter(v for row in region.cells for v in row if v is not None)
    singles = [color for color, n in counts.items() if n == 1]
    if len(singles) != 1:
        return None
    for r, row in enumerate(region.cells):
        for c, v in enumerate(row):
            if v == singles[0]:
                return v, r, c
    return None


def key_color(region: RegionValue, arg: Any) -> int:
    found = _key_position(region)
    return found[0] if found else NO_KEY


def key_row(region: RegionValue, arg: Any) -> int:
    found = _key_position(region)
    return found[1] if found else 0


def key_col(region: RegionValue, arg: Any) -> int:
    found = _key_position(region)
    return found[2] if found else 0
