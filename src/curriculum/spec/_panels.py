"""Panel-grid transforms (ADR 0106): a grid cut into panels by full separator
lines, with per-panel properties (uniform, background, shape mask). Pure grid
logic, no library imports."""
from collections import Counter
from typing import List, Optional, Tuple

from src.curriculum.grid import Grid
from src.curriculum.spec import vocabulary as vocab
from src.curriculum.spec._expressions import InterpreterError
from src.curriculum.spec._region_value import RegionValue

Span = Tuple[int, int]


def _spans(separators: List[int], total: int) -> List[Span]:
    cuts, spans, start = set(separators), [], 0
    for i in range(total + 1):
        if i == total or i in cuts:
            if i > start:
                spans.append((start, i))
            start = i + 1
    return spans


def find_panels(cells: Grid) -> Optional[Tuple[List[Span], List[Span]]]:
    """Row and column spans of the panels, cut by the lowest color that fills
    at least one whole row and one whole column; None when there is none."""
    height, width = len(cells), len(cells[0])
    for color in sorted({v for row in cells for v in row}):
        rows = [y for y in range(height) if all(v == color for v in cells[y])]
        cols = [x for x in range(width) if all(cells[y][x] == color for y in range(height))]
        if rows and cols:
            row_spans, col_spans = _spans(rows, height), _spans(cols, width)
            if row_spans and col_spans and len(row_spans) * len(col_spans) > 1:
                return row_spans, col_spans
    return None


def panel_cells(cells: Grid, rows: Span, cols: Span) -> List[List[int]]:
    return [list(cells[y][cols[0]:cols[1]]) for y in range(*rows)]


def panel_background(block: List[List[int]]) -> int:
    return Counter(v for row in block for v in row).most_common(1)[0][0]


def panel_uniform_color(block: List[List[int]]) -> Optional[int]:
    values = {v for row in block for v in row}
    return values.pop() if len(values) == 1 else None


def _require_panels(region: RegionValue, name: str):
    found = find_panels(region.cells)
    if found is None:
        raise InterpreterError(f"{name}: no separator lines found")
    return found


def _with_cells(region: RegionValue, cells: Grid) -> RegionValue:
    return RegionValue(row0=region.row0, col0=region.col0, rows=len(cells), cols=len(cells[0]), cells=cells)


def summarize_uniform_panels(region: RegionValue, op: vocab.PanelSummary) -> RegionValue:
    """One pixel per panel over the bounding box of the uniform panels."""
    row_spans, col_spans = _require_panels(region, "panel_summary")
    solid = {}
    for i, rows in enumerate(row_spans):
        for j, cols in enumerate(col_spans):
            color = panel_uniform_color(panel_cells(region.cells, rows, cols))
            if color is not None:
                solid[(i, j)] = color
    if not solid:
        raise InterpreterError("panel_summary: no uniform panel")
    i0, i1 = min(i for i, _ in solid), max(i for i, _ in solid)
    j0, j1 = min(j for _, j in solid), max(j for _, j in solid)
    cells = [[solid.get((i, j), op.fill) for j in range(j0, j1 + 1)] for i in range(i0, i1 + 1)]
    return _with_cells(region, cells)


def _partner_index(axis: str, i: int, j: int) -> Tuple[int, int]:
    return (i, 1 - j) if axis == "row" else (1 - i, j)


def _paint_swapped(out: Grid, region: RegionValue, target, source) -> None:
    (t_rows, t_cols), (s_rows, s_cols) = target, source
    t_block = panel_cells(region.cells, t_rows, t_cols)
    s_block = panel_cells(region.cells, s_rows, s_cols)
    if len(t_block) != len(s_block) or len(t_block[0]) != len(s_block[0]):
        raise InterpreterError("panel_swap: partner panels differ in size")
    t_bg, s_bg = panel_background(t_block), panel_background(s_block)
    for y, row in enumerate(s_block):
        for x, value in enumerate(row):
            out[t_rows[0] + y][t_cols[0] + x] = s_bg if value != s_bg else t_bg


def swap_panel_masks(region: RegionValue, op: vocab.PanelSwap) -> RegionValue:
    """Each panel takes its partner's shape mask, repainted in the partner's
    own background color (partner: the other panel of a pair along `axis`)."""
    row_spans, col_spans = _require_panels(region, "panel_swap")
    expected = (len(row_spans), len(col_spans))
    if (expected[1] if op.axis == "row" else expected[0]) != 2:
        raise InterpreterError("panel_swap: axis does not hold exactly two panels")
    out = [list(row) for row in region.cells]
    for i, rows in enumerate(row_spans):
        for j, cols in enumerate(col_spans):
            pi, pj = _partner_index(op.axis, i, j)
            _paint_swapped(out, region, (rows, cols), (row_spans[pi], col_spans[pj]))
    return _with_cells(region, out)
