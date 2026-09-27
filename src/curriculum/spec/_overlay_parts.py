"""`OverlayParts` transform (ADR 0094): equal-part split of a region and a
mask -> color lookup per position. Pure grid logic, no library imports."""
from typing import List

from src.curriculum.spec import vocabulary as vocab
from src.curriculum.spec._expressions import InterpreterError
from src.curriculum.spec._region_value import RegionValue


def axis_starts(total: int, count: int, divider: bool) -> List[int]:
    """Start offsets of `count` equal parts along one axis of length `total`."""
    gap = 1 if divider else 0
    size = (total - gap * (count - 1)) // count
    if size < 1 or size * count + gap * (count - 1) != total:
        raise InterpreterError(f"overlay_parts: axis of {total} does not split into {count} parts")
    return [i * (size + gap) for i in range(count)]


def _part_size(total: int, count: int, divider: bool) -> int:
    return (total - (count - 1 if divider else 0)) // count


def overlay_parts_region(region: RegionValue, op: vocab.OverlayParts) -> RegionValue:
    rows = axis_starts(region.rows, op.n_rows, op.divider)
    cols = axis_starts(region.cols, op.n_cols, op.divider)
    height, width = _part_size(region.rows, op.n_rows, op.divider), _part_size(region.cols, op.n_cols, op.divider)
    table = dict(op.table)
    origins = [(r, c) for r in rows for c in cols]
    cells = [[_lookup(region, origins, r, c, op, table) for c in range(width)] for r in range(height)]
    return RegionValue(row0=region.row0, col0=region.col0, rows=height, cols=width, cells=cells)


def _lookup(region: RegionValue, origins, r: int, c: int, op: vocab.OverlayParts, table: dict) -> int:
    mask = tuple(region.cells[r0 + r][c0 + c] != op.background for r0, c0 in origins)
    if mask not in table:
        raise InterpreterError(f"overlay_parts: mask {mask} has no table entry")
    return table[mask]
