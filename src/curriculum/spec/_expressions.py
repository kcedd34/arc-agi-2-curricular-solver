"""Evaluates Expr/Predicate nodes from vocabulary.py against an Environment.

Split out of interpreter.py so each file stays under the one-file/one-
responsibility convention (ADR 0062, RN-CUR-27 implementation split).
"""
from typing import Any, Dict

from src.curriculum.grid import grid_dims
from src.curriculum.spec import vocabulary as vocab
from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._list_memo import list_memo
from src.curriculum.spec._object_border import has_interior
from src.curriculum.spec._object_holes import has_hole
from src.curriculum.spec._region_value import RegionValue

_BINOPS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "//": lambda a, b: a // b,
    "%": lambda a, b: a % b,
    "==": lambda a, b: int(a == b),
}


def eval_expr(expr: vocab.Expr, env: Any) -> Any:
    if isinstance(expr, (int, str)):
        return expr
    if isinstance(expr, vocab.Ref):
        return env.bound[expr.name]
    if isinstance(expr, vocab.Attr):
        return _attr_of(eval_expr(expr.base, env), expr.attr)
    if isinstance(expr, vocab.Count):
        return len(eval_expr(expr.list_ref, env))
    if isinstance(expr, vocab.BinOp):
        left = eval_expr(expr.left, env)
        right = eval_expr(expr.right, env)
        return _BINOPS[expr.op](left, right)
    if isinstance(expr, vocab.CellAt):
        return _eval_cell_at(expr, env)
    if isinstance(expr, vocab.Measure):
        return _eval_measure(expr, env)
    if isinstance(expr, vocab.Extremum):
        return _eval_extremum(expr, env)
    if isinstance(expr, vocab.Derive):
        return _eval_derive(expr, env)
    if isinstance(expr, vocab.TableLookup):
        return _eval_table_lookup(expr, env)
    raise InterpreterError(f"unknown expression: {expr!r}")


def _eval_measure(expr: vocab.Measure, env: Any) -> int:
    from src.curriculum.spec import _measures
    from src.curriculum.spec import _regions as regions

    region = regions.resolve_bound_region(expr.region, env)
    return _measures.measure_value(region, expr.name, eval_expr(expr.arg, env))


def _eval_extremum(expr: vocab.Extremum, env: Any) -> int:
    from src.curriculum.spec import _derive

    if expr.mode not in ("min", "max"):
        raise InterpreterError(f"extremum: unknown mode {expr.mode!r}")
    items = eval_expr(expr.list_ref, env)
    return _derive.derive_from_regions(items, expr.mode, expr.name, eval_expr(expr.arg, env))


def _eval_derive(expr: vocab.Derive, env: Any) -> int:
    from src.curriculum.spec import _derive

    source = eval_expr(expr.source, env)
    if expr.op in _derive.GRID_OPS:
        return _derive.derive_from_grid(source, expr.op, eval_expr(expr.background, env))
    return _derive.derive_from_regions(source, expr.op, expr.name, eval_expr(expr.arg, env))


def _eval_table_lookup(expr: vocab.TableLookup, env: Any) -> int:
    from src.curriculum.spec import _derive

    key = tuple(eval_expr(k, env) for k in expr.keys)
    return _derive.table_lookup(expr.table, key)


def _eval_cell_at(expr: vocab.CellAt, env: Any) -> int:
    base = eval_expr(expr.grid, env)
    cells = base.cells if isinstance(base, RegionValue) else base
    rows, cols = grid_dims(cells)
    row = eval_expr(expr.row, env)
    col = eval_expr(expr.col, env)
    if not (0 <= row < rows and 0 <= col < cols):
        raise InterpreterError(
            f"cell_at: ({row}, {col}) out of bounds for a {rows}x{cols} grid"
        )
    return cells[row][col]


def _attr_of(base: Any, attr: str) -> int:
    if attr in ("rows", "cols"):
        cells = base.cells if isinstance(base, RegionValue) else base
        rows, cols = grid_dims(cells)
        return rows if attr == "rows" else cols
    if attr in ("row", "col"):
        if not isinstance(base, RegionValue):
            raise ValueError(f"attribute {attr!r} requires a region value")
        return base.row0 if attr == "row" else base.col0
    if attr == "color":
        return _single_member_color(base)
    raise ValueError(f"unknown attribute: {attr!r}")


def eval_predicate(pred: vocab.Predicate, env: Any) -> bool:
    if isinstance(pred, vocab.IsBackground):
        value = _scalar_color(eval_expr(pred.value, env))
        return value == eval_expr(pred.background, env)
    if isinstance(pred, vocab.ColorEq):
        a = _scalar_color(eval_expr(pred.a, env))
        b = _scalar_color(eval_expr(pred.b, env))
        return a == b
    if isinstance(pred, vocab.ColorIn):
        return eval_expr(pred.color, env) in eval_expr(pred.color_set, env)
    if isinstance(pred, vocab.CountEq):
        return len(eval_expr(pred.list_ref, env)) == eval_expr(pred.n, env)
    if isinstance(pred, vocab.IsIsolated):
        grid = eval_expr(pred.grid, env)
        cells = grid.cells if isinstance(grid, RegionValue) else grid
        row = eval_expr(pred.row, env)
        col = eval_expr(pred.col, env)
        background = eval_expr(pred.background, env)
        return is_isolated_cell(cells, row, col, background)
    return _eval_region_predicate(pred, env)


def is_isolated_cell(grid: Any, row: int, col: int, background: int) -> bool:
    """True iff (row, col) is non-background and has no orthogonally
    adjacent cell of the same color. Shared by the IsIsolated predicate
    and SegmentTo's region resolution (_regions.py), both of which need
    the same isolated-marker-cell test (ADR 0066)."""
    rows, cols = grid_dims(grid)
    if not (0 <= row < rows and 0 <= col < cols):
        raise InterpreterError(
            f"is_isolated: ({row}, {col}) out of bounds for a {rows}x{cols} grid"
        )
    color = grid[row][col]
    if color == background:
        return False
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = row + dr, col + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == color:
            return False
    return True


def _eval_region_predicate(pred: vocab.Predicate, env: Any) -> bool:
    from src.curriculum.spec import _regions as regions

    if isinstance(pred, vocab.SizeGt):
        region = regions.resolve_bound_region(pred.region, env)
        return _region_true_size(region) > eval_expr(pred.n, env)
    if isinstance(pred, vocab.SizeEq):
        region = regions.resolve_bound_region(pred.region, env)
        return _region_true_size(region) == eval_expr(pred.n, env)
    if isinstance(pred, vocab.TouchesBorder):
        region = regions.resolve_bound_region(pred.region, env)
        grid = eval_expr(pred.grid, env)
        return _touches_border(region, grid)
    if isinstance(pred, vocab.IsLargest):
        return _is_extreme(pred.region, pred.list_ref, env, maximize=True)
    if isinstance(pred, vocab.IsSmallest):
        return _is_extreme(pred.region, pred.list_ref, env, maximize=False)
    if isinstance(pred, vocab.ObjectColorEq):
        region = regions.resolve_bound_region(pred.region, env)
        color = _object_single_color(region)
        return color is not None and color == eval_expr(pred.color, env)
    if isinstance(pred, vocab.HasUniqueColor):
        return _has_unique_color(pred.region, pred.list_ref, env)
    if isinstance(pred, vocab.HasHole):
        return _memoized_flag(regions.resolve_bound_region(pred.region, env), "has_hole", has_hole)
    if isinstance(pred, vocab.HasInterior):
        return _memoized_flag(
            regions.resolve_bound_region(pred.region, env), "has_interior", has_interior
        )
    raise ValueError(f"unknown predicate: {pred!r}")


def _region_true_size(region: RegionValue) -> int:
    """Count of cells that are part of the object itself, not the
    bounding-box area - a bbox may include non-member (None) cells for a
    non-rectangular object (object pack Section 3.2). Memoized per region
    (ADR 0090)."""
    memo = region.memo
    size = memo.get("size")
    if size is None:
        size = memo["size"] = sum(1 for row in region.cells for v in row if v is not None)
    return size


def _object_single_color(region: RegionValue):
    """The region's own single color, or None when it spans more than one
    color (object pack Section 3.2's object representation: `color` is
    only defined for a monochromatic object). Memoized per region."""
    memo = region.memo
    if "color" not in memo:
        colors = {v for row in region.cells for v in row if v is not None}
        memo["color"] = next(iter(colors)) if len(colors) == 1 else None
    return memo["color"]


def _memoized_flag(region: RegionValue, key: str, compute) -> bool:
    memo = region.memo
    if key not in memo:
        memo[key] = compute(region.cells)
    return memo[key]


def _unique_extreme(items: list, maximize: bool):
    """The one item at the extreme true size, or None on a tie/empty list."""
    memo = list_memo(items)
    key = "max_item" if maximize else "min_item"
    if key not in memo:
        sizes = [_region_true_size(item) for item in items]
        found = None
        if sizes:
            target = max(sizes) if maximize else min(sizes)
            matches = [item for item, size in zip(items, sizes) if size == target]
            found = matches[0] if len(matches) == 1 else None
        memo[key] = found
    return memo[key]


def _is_extreme(region_ref: vocab.Region, list_ref: vocab.Expr, env: Any, maximize: bool) -> bool:
    """Never breaks a tie silently (object pack Section 3.2.5): true only
    when `region_ref` is the unique item at the extreme true size among
    `list_ref`."""
    from src.curriculum.spec import _regions as regions

    region = regions.resolve_bound_region(region_ref, env)
    items = eval_expr(list_ref, env)
    return _unique_extreme(items, maximize) is region


def _items_by_color(items: list) -> Dict[Any, list]:
    memo = list_memo(items)
    if "by_color" not in memo:
        by_color: Dict[Any, list] = {}
        for item in items:
            by_color.setdefault(_object_single_color(item), []).append(item)
        memo["by_color"] = by_color
    return memo["by_color"]


def _has_unique_color(region_ref: vocab.Region, list_ref: vocab.Expr, env: Any) -> bool:
    from src.curriculum.spec import _regions as regions

    region = regions.resolve_bound_region(region_ref, env)
    color = _object_single_color(region)
    if color is None:
        return False
    sharing = _items_by_color(eval_expr(list_ref, env)).get(color, [])
    return len(sharing) == 1 and sharing[0] is region


def _touches_border(region: RegionValue, grid: Any) -> bool:
    rows, cols = grid_dims(grid)
    return (
        region.row0 == 0
        or region.col0 == 0
        or region.row0 + region.rows == rows
        or region.col0 + region.cols == cols
    )


def _single_member_color(base: Any) -> int:
    """The one color shared by every member cell of a region (ADR 0098)."""
    if not isinstance(base, RegionValue):
        raise ValueError("attribute 'color' requires a region value")
    colors = {v for row in base.cells for v in row if v is not None}
    if len(colors) != 1:
        raise InterpreterError(f"color: region has {len(colors)} colors, expected exactly 1")
    return next(iter(colors))


def _scalar_color(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, RegionValue):
        if value.rows == 1 and value.cols == 1:
            return value.cells[0][0]
        return _dominant_color(value)
    raise ValueError(f"cannot resolve a scalar color from: {value!r}")


def _dominant_color(region: RegionValue) -> int:
    counts: Dict[int, int] = {}
    for row in region.cells:
        for v in row:
            if v is not None:
                counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)
