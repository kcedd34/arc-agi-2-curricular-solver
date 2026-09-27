"""Pure-Python prediction of one stamp candidate on one train input (ADR 0109).
A pre-filter only: it mirrors `lowering_stamp` so that most candidates are
dropped without running the interpreter; survivors are still verified by it."""
from typing import List, Optional

from src.curriculum.grid import Grid
from src.curriculum.library.derived.lowering_stamp import ALL_PAIRS, ERASE_ALL, ERASE_TEMPLATES, KEY_ALIGN
from src.curriculum.spec._key_measures import key_col, key_color, key_row
from src.curriculum.spec._region_value import RegionValue


def _paint(out: Grid, region: RegionValue, dr: int, dc: int) -> bool:
    rows, cols = len(out), len(out[0])
    for r, row in enumerate(region.cells):
        for c, value in enumerate(row):
            if value is None:
                continue
            rr, cc = region.row0 + r + dr, region.col0 + c + dc
            if not (0 <= rr < rows and 0 <= cc < cols):
                return False
            out[rr][cc] = value
    return True


def _pin(region: RegionValue, align: str) -> tuple:
    if align == KEY_ALIGN:
        return region.row0 + key_row(region, 0), region.col0 + key_col(region, 0)
    return region.row0, region.col0


def _matches(template: RegionValue, anchor: RegionValue, pairing: str) -> bool:
    return pairing == ALL_PAIRS or key_color(template, 0) == key_color(anchor, 0)


def predict_stamp(
    grid: Grid, regions: List[RegionValue], templates: List[RegionValue], anchors: List[RegionValue],
    options: tuple, background: int,
) -> Optional[Grid]:
    align, pairing, erase = options
    out = [list(row) for row in grid]
    erased = regions if erase == ERASE_ALL else templates if erase == ERASE_TEMPLATES else []
    for region in erased:
        _paint(out, RegionValue(region.row0, region.col0, region.rows, region.cols,
                                [[background if v is not None else None for v in row] for row in region.cells]), 0, 0)
    for anchor in anchors:
        for template in (t for t in templates if _matches(t, anchor, pairing)):
            (ar, ac), (tr, tc) = _pin(anchor, align), _pin(template, align)
            if not _paint(out, template, ar - tr, ac - tc):
                return None
    return out
