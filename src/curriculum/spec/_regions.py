"""Resolves Region nodes (RegionRef/BlockAt) against an Environment (ADR 0062).

Split out of interpreter.py per the one-file/one-responsibility convention
and to avoid a circular import with `_expressions.py` (`eval_expr` is
needed here for BlockAt's row/col expressions).
"""
from typing import Any, List, Tuple

from src.curriculum.grid import grid_dims
from src.curriculum.spec import vocabulary as vocab
from src.curriculum.spec._region_value import RegionValue

_DIRECTION_DELTAS = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}


def resolve_bound_region(region: vocab.Region, env: Any) -> RegionValue:
    if isinstance(region, vocab.RegionRef):
        value = env.bound[region.name]
        if not isinstance(value, RegionValue):
            raise ValueError(f"bound name {region.name!r} is not a region")
        return value
    if isinstance(region, vocab.BlockAt):
        return _resolve_block_at(region, env)
    if isinstance(region, vocab.SegmentTo):
        return _resolve_segment_to(region, env)
    if isinstance(region, vocab.SlideTo):
        return _resolve_slide_to(region, env)
    if isinstance(region, vocab.AtOrigin):
        return _resolve_at_origin(region, env)
    if isinstance(region, vocab.WholeGrid):
        return _resolve_whole_grid(region, env)
    if isinstance(region, vocab.Between):
        return _resolve_between(region, env)
    if isinstance(region, vocab.CornerCell):
        return _resolve_corner_cell(region, env)
    raise ValueError(f"unknown region: {region!r}")


def _resolve_block_at(region: vocab.BlockAt, env: Any) -> RegionValue:
    from src.curriculum.spec._expressions import eval_expr

    if env.output_grid is None:
        raise ValueError("block_at used before shape_out")
    if not env.active_extents:
        raise ValueError("block_at used outside a for_each over a partition")
    extent_rows, extent_cols = env.active_extents[-1]
    out_rows = len(env.output_grid)
    out_cols = len(env.output_grid[0])
    if out_rows % extent_rows != 0 or out_cols % extent_cols != 0:
        raise ValueError(
            "block_at: output shape is not an exact multiple of the "
            "partition extent (RN-CUR-27 block-size inference)"
        )
    block_h = out_rows // extent_rows
    block_w = out_cols // extent_cols
    row_index = eval_expr(region.row, env)
    col_index = eval_expr(region.col, env)
    row0 = row_index * block_h
    col0 = col_index * block_w
    cells = [
        row[col0 : col0 + block_w]
        for row in env.output_grid[row0 : row0 + block_h]
    ]
    return RegionValue(row0=row0, col0=col0, rows=block_h, cols=block_w, cells=cells)


def _empty_region() -> RegionValue:
    return RegionValue(row0=0, col0=0, rows=0, cols=0, cells=[])


_STOP_CONDITIONS = ("same_color_isolated", "border", "any_obstacle")


def _resolve_segment_to(region: vocab.SegmentTo, env: Any) -> RegionValue:
    from src.curriculum.spec._expressions import InterpreterError, eval_expr

    grid_value = eval_expr(region.grid, env)
    grid = grid_value.cells if isinstance(grid_value, RegionValue) else grid_value
    row = eval_expr(region.from_row, env)
    col = eval_expr(region.from_col, env)
    background = eval_expr(region.background, env)
    if region.direction not in _DIRECTION_DELTAS:
        raise ValueError(f"segment_to: unknown direction {region.direction!r}")
    if region.stop_condition not in _STOP_CONDITIONS:
        raise ValueError(f"segment_to: unknown stop_condition {region.stop_condition!r}")
    rows, cols = grid_dims(grid)
    if not (0 <= row < rows and 0 <= col < cols):
        raise InterpreterError(
            f"segment_to: origin ({row}, {col}) out of bounds for a {rows}x{cols} grid"
        )
    dr, dc = _DIRECTION_DELTAS[region.direction]
    origin_color = grid[row][col]
    between: List[Tuple[int, int]] = []
    r, c = row + dr, col + dc
    while 0 <= r < rows and 0 <= c < cols:
        if grid[r][c] == background:
            between.append((r, c))
            r += dr
            c += dc
            continue
        return _resolve_obstacle_stop(
            region.stop_condition, between, grid, r, c, origin_color, background
        )
    return _resolve_border_stop(region.stop_condition, between, grid)


def _resolve_obstacle_stop(
    stop_condition: str,
    between: List[Tuple[int, int]],
    grid: Any,
    r: int,
    c: int,
    origin_color: int,
    background: int,
) -> RegionValue:
    """Hitting a non-background cell during the scan (before any border)."""
    from src.curriculum.spec._expressions import is_isolated_cell

    if stop_condition == "any_obstacle":
        return _between_region(between, grid)
    if stop_condition == "same_color_isolated":
        if grid[r][c] == origin_color and is_isolated_cell(grid, r, c, background):
            return _between_region(between, grid)
        return _empty_region()
    # "border": an obstacle reached before leaving the grid means the
    # border was never actually hit, so this stop condition is not met.
    return _empty_region()


def _resolve_border_stop(
    stop_condition: str, between: List[Tuple[int, int]], grid: Any
) -> RegionValue:
    """The scan left the grid without ever hitting a non-background cell."""
    if stop_condition == "border":
        return _between_region(between, grid)
    return _empty_region()


_SLIDE_STOPS = ("border", "contact", "settle")
_CONTACT_STOPS = ("contact", "settle")


def _slide_scene(region: vocab.SlideTo, env: Any, background: Any):
    """Collision scene: the output under construction for "settle" (unset
    cells count as background), otherwise `region.grid`."""
    from src.curriculum.spec._expressions import eval_expr

    if region.stop == "settle":
        if env.output_grid is None:
            raise ValueError("slide: settle used before shape_out")
        return [[background if v is None else v for v in row] for row in env.output_grid]
    grid_value = eval_expr(region.grid, env)
    return grid_value.cells if isinstance(grid_value, RegionValue) else grid_value


def _slide_delta(region: vocab.SlideTo, base: RegionValue, env: Any) -> Tuple[int, int]:
    """Fixed direction, or (`direction == "toward"`) the axis-aligned one
    toward `region.target` (ADR 0098)."""
    from src.curriculum.spec._expressions import eval_expr
    from src.curriculum.spec._toward import toward_target

    if region.direction == "toward":
        return toward_target(base, eval_expr(region.target, env))[0]
    if region.direction not in _DIRECTION_DELTAS:
        raise ValueError(f"slide: unknown direction {region.direction!r}")
    return _DIRECTION_DELTAS[region.direction]


def _member_offsets(base: RegionValue) -> List[Tuple[int, int]]:
    return [
        (r, c)
        for r in range(base.rows)
        for c in range(base.cols)
        if base.cells[r][c] is not None
    ]


def _in_bounds(absolute: List[Tuple[int, int]], rows: int, cols: int) -> bool:
    return all(0 <= r < rows and 0 <= c < cols for r, c in absolute)


def _resolve_slide_to(region: vocab.SlideTo, env: Any) -> RegionValue:
    """Greedily steps `region.region` one cell at a time along `direction`
    (object pack Section 3.3's `slide(region, direction, stop)`). The
    object's own pre-slide cells are excluded from the "contact" collision
    check so it never registers contact with the trail it is vacating.
    After the stop, `extra` more steps are taken that ignore collisions
    (still bounded by the grid), e.g. to overwrite the obstacle (ADR 0098)."""
    from src.curriculum.spec._expressions import eval_expr

    base = resolve_bound_region(region.region, env)
    if region.stop not in _SLIDE_STOPS:
        raise ValueError(f"slide: unknown stop {region.stop!r}")
    offsets = _member_offsets(base)
    if not offsets:
        return base

    background = eval_expr(region.background, env)
    grid = _slide_scene(region, env, background)
    rows, cols = grid_dims(grid)
    dr, dc = _slide_delta(region, base, env)
    own_cells = {(base.row0 + r, base.col0 + c) for r, c in offsets}

    row0, col0 = base.row0, base.col0
    while True:
        absolute = [(row0 + dr + r, col0 + dc + c) for r, c in offsets]
        if not _in_bounds(absolute, rows, cols):
            break
        if region.stop in _CONTACT_STOPS and any(
            grid[r][c] != background and (r, c) not in own_cells for r, c in absolute
        ):
            break
        row0, col0 = row0 + dr, col0 + dc
    for _ in range(eval_expr(region.extra, env)):
        absolute = [(row0 + dr + r, col0 + dc + c) for r, c in offsets]
        if not _in_bounds(absolute, rows, cols):
            break
        row0, col0 = row0 + dr, col0 + dc

    return RegionValue(row0=row0, col0=col0, rows=base.rows, cols=base.cols, cells=base.cells)


def _resolve_at_origin(region: vocab.AtOrigin, env: Any) -> RegionValue:
    base = resolve_bound_region(region.region, env)
    return RegionValue(row0=0, col0=0, rows=base.rows, cols=base.cols, cells=base.cells)


def _resolve_whole_grid(region: vocab.WholeGrid, env: Any) -> RegionValue:
    from src.curriculum.spec._expressions import eval_expr

    grid = eval_expr(region.grid, env)
    grid = grid.cells if isinstance(grid, RegionValue) else grid
    rows, cols = grid_dims(grid)
    return RegionValue(row0=0, col0=0, rows=rows, cols=cols, cells=grid)


def _resolve_between(region: vocab.Between, env: Any) -> RegionValue:
    """Strictly-interior span of a one-row/one-column region (ADR 0098)."""
    from src.curriculum.spec._expressions import InterpreterError

    base = resolve_bound_region(region.region, env)
    if base.rows != 1 and base.cols != 1:
        raise InterpreterError(f"between: region {base.rows}x{base.cols} is not a line")
    length = max(base.rows, base.cols)
    if length <= 2:
        return _empty_region()
    if base.rows == 1:
        rows, cols, row0, col0 = 1, length - 2, base.row0, base.col0 + 1
    else:
        rows, cols, row0, col0 = length - 2, 1, base.row0 + 1, base.col0
    return RegionValue(row0=row0, col0=col0, rows=rows, cols=cols, cells=[[0] * cols for _ in range(rows)])


def _resolve_corner_cell(region: vocab.CornerCell, env: Any) -> RegionValue:
    """Top-left diagonal neighbour cell of the base region's bbox (Round 20)."""
    base = resolve_bound_region(region.region, env)
    row, col = base.row0 - 1, base.col0 - 1
    rows, cols = grid_dims(env.output_grid)
    if not (0 <= row < rows and 0 <= col < cols):
        return _empty_region()
    return RegionValue(row0=row, col0=col, rows=1, cols=1, cells=[[0]])


def _between_region(between: List[Tuple[int, int]], grid) -> RegionValue:
    if not between:
        return _empty_region()
    rows = sorted({r for r, _ in between})
    cols = sorted({c for _, c in between})
    row0, col0 = rows[0], cols[0]
    cells = [[grid[r][c] for c in cols] for r in rows]
    return RegionValue(
        row0=row0, col0=col0, rows=len(rows), cols=len(cols), cells=cells
    )
