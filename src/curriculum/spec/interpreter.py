"""Generic trace interpreter for the declarative-step vocabulary (ADR 0062).

Executes a `Step` sequence against an input grid, producing the output
grid plus a full execution trace (RN-CUR-14: a desk check never needs to
read primitive code, only this module and vocabulary.py). This module
must never import anything from `src.curriculum.library` (proven by
`tests/curriculum/spec/test_interpreter.py::test_interpreter_independence`)
so a trace stays meaningful no matter how large the primitive library
grows.

Trace granularity (an RN-CUR-27 implementation decision, not spelled out
verbatim by ADR 0062's own trace-schema text): every executed `Step`
instance produces exactly one trace entry, in real execution order,
including composite steps (`for_each`, `branch`) and every step inside a
loop body/taken branch. A `for_each` over N elements therefore yields one
entry for the loop itself plus N * (entries per body execution).
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.curriculum.grid import Grid, grid_dims
from src.curriculum.spec import vocabulary as vocab
from src.curriculum.spec import work_meter
from src.curriculum.spec._expressions import InterpreterError, eval_expr, eval_predicate
from src.curriculum.spec._for_each_order import ordered_items
from src.curriculum.spec._object_border import interior_positions
from src.curriculum.spec._op_params import resolve_op_params
from src.curriculum.spec._object_halo import halo_region
from src.curriculum.spec._object_holes import enclosed_positions
from src.curriculum.spec._overlay_parts import overlay_parts_region
from src.curriculum.spec._panels import summarize_uniform_panels, swap_panel_masks
from src.curriculum.spec._region_value import RegionContext, RegionValue
from src.curriculum.spec._segments import col_segments, row_segments
from src.curriculum.spec._select_where import exec_select_where
from src.curriculum.spec._regions import resolve_bound_region

TraceEntry = Dict[str, Any]


@dataclass
class Environment:
    bound: Dict[str, Any] = field(default_factory=dict)
    output_grid: Optional[List[List[Optional[int]]]] = None
    partition_extents: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    active_extents: List[Tuple[int, int]] = field(default_factory=list)
    trace: List[TraceEntry] = field(default_factory=list)
    _step_counter: int = 0

    def next_step_number(self) -> int:
        self._step_counter += 1
        return self._step_counter

    def log(
        self,
        op: str,
        region: Any = None,
        condition: Any = None,
        result: Any = None,
        value: Any = None,
    ) -> None:
        self.trace.append(
            {
                "step": self.next_step_number(),
                "op": op,
                "region": region,
                "condition": condition,
                "result": result,
                "value": value,
            }
        )


def run(steps: List[vocab.Step], input_grid: Grid) -> Tuple[Grid, List[TraceEntry]]:
    """Execute a full step sequence against input_grid.

    Returns (output_grid, trace). Raises InterpreterError if the sequence
    never calls compose() (an incomplete program has no defined output).
    """
    work_meter.charge(max(1, len(input_grid) * len(input_grid[0])))
    env = Environment(bound={"input": input_grid})
    execute_steps(steps, env)
    if env.output_grid is None:
        raise InterpreterError("step sequence never called shape_out()")
    if any(cell is None for row in env.output_grid for cell in row):
        raise InterpreterError("step sequence never called compose()")
    return env.output_grid, env.trace


def execute_steps(steps: List[vocab.Step], env: Environment) -> None:
    for step in steps:
        execute_step(step, env)


def execute_step(step: vocab.Step, env: Environment) -> None:
    if isinstance(step, vocab.Bind):
        _exec_bind(step, env)
    elif isinstance(step, vocab.ShapeOut):
        _exec_shape_out(step, env)
    elif isinstance(step, vocab.Partition):
        _exec_partition(step, env)
    elif isinstance(step, vocab.Correspond):
        _exec_correspond(step, env)
    elif isinstance(step, vocab.ForEach):
        _exec_for_each(step, env)
    elif isinstance(step, vocab.Test):
        _exec_test(step, env)
    elif isinstance(step, vocab.Branch):
        _exec_branch(step, env)
    elif isinstance(step, vocab.Emit):
        _exec_emit(step, env)
    elif isinstance(step, vocab.Transform):
        _exec_transform(step, env)
    elif isinstance(step, vocab.Compose):
        _exec_compose(step, env)
    elif isinstance(step, vocab.Seed):
        _exec_seed(step, env)
    elif isinstance(step, vocab.SelectWhere):
        exec_select_where(step, env)
    else:
        raise InterpreterError(f"unknown step: {step!r}")


def _exec_bind(step: vocab.Bind, env: Environment) -> None:
    value = eval_expr(step.value, env)
    env.bound[step.name] = value
    env.log("bind", result=step.name, value=_loggable(value))


def _exec_shape_out(step: vocab.ShapeOut, env: Environment) -> None:
    rows = eval_expr(step.rows, env)
    cols = eval_expr(step.cols, env)
    if rows <= 0 or cols <= 0:
        raise InterpreterError(f"shape_out: invalid shape ({rows}, {cols})")
    env.output_grid = [[None for _ in range(cols)] for _ in range(rows)]
    env.log("shape_out", value={"rows": rows, "cols": cols})


def _exec_partition(step: vocab.Partition, env: Environment) -> None:
    if isinstance(step.kind, vocab.IndexGrid):
        regions = _partition_grid(None, step.kind)
        env.bound[step.result_name] = regions
        env.partition_extents[step.result_name] = (step.kind.rows, step.kind.cols)
    else:
        source = eval_expr(step.source, env)
        grid = source.cells if isinstance(source, RegionValue) else source
        regions = _partition_input_cached(grid, step.kind, env)
        env.bound[step.result_name] = regions
        rows, cols = grid_dims(grid)
        env.partition_extents[step.result_name] = (rows, cols)
    env.log(
        "partition",
        region=_expr_repr(step.source),
        result=step.result_name,
        value=len(regions),
    )


_PARTITION_CACHE: Dict[Tuple[int, Any], Tuple[Grid, List[RegionValue]]] = {}
_PARTITION_CACHE_MAX = 256


def _partition_input_cached(grid: Grid, kind: vocab.PartitionKind, env: Environment) -> List[RegionValue]:
    """Object partitions of the run's own input grid are recomputed for
    every candidate program over the same task; cache them (ADR 0090). Only
    the immutable input grid is cached (a strong ref keeps `id` unambiguous);
    intermediate grids are partitioned fresh."""
    if not isinstance(kind, vocab.Objects) or grid is not env.bound.get("input"):
        return _partition_grid(grid, kind)
    key = (id(grid), kind)
    entry = _PARTITION_CACHE.get(key)
    if entry is None or entry[0] is not grid:
        if len(_PARTITION_CACHE) >= _PARTITION_CACHE_MAX:
            _PARTITION_CACHE.clear()
        entry = (grid, _partition_grid(grid, kind))
        _PARTITION_CACHE[key] = entry
    return entry[1]


def _partition_grid(grid: Optional[Grid], kind: vocab.PartitionKind) -> List[RegionValue]:
    regions = _partition_regions(grid, kind)
    if grid is not None and not isinstance(kind, vocab.IndexGrid):
        _attach_context(regions, grid_dims(grid))
    return regions


def _attach_context(regions: List[RegionValue], dims: Tuple[int, int]) -> None:
    shared: Dict[str, Any] = {}
    for index, region in enumerate(regions):
        region.ctx = RegionContext(regions, index, dims, shared)


def _partition_regions(grid: Optional[Grid], kind: vocab.PartitionKind) -> List[RegionValue]:
    if isinstance(kind, vocab.IndexGrid):
        return [
            RegionValue(row0=r, col0=c, rows=1, cols=1, cells=[[0]])
            for r in range(kind.rows)
            for c in range(kind.cols)
        ]
    rows, cols = grid_dims(grid)
    if isinstance(kind, vocab.Cells):
        return [
            RegionValue(row0=r, col0=c, rows=1, cols=1, cells=[[grid[r][c]]])
            for r in range(rows)
            for c in range(cols)
        ]
    if isinstance(kind, vocab.Rows):
        return [
            RegionValue(row0=r, col0=0, rows=1, cols=cols, cells=[grid[r][:]])
            for r in range(rows)
        ]
    if isinstance(kind, vocab.Cols):
        return [
            RegionValue(
                row0=0, col0=c, rows=rows, cols=1, cells=[[grid[r][c]] for r in range(rows)]
            )
            for c in range(cols)
        ]
    if isinstance(kind, vocab.Blocks):
        return _partition_blocks(grid, kind.h, kind.w)
    if isinstance(kind, vocab.Objects):
        return _partition_objects(grid, kind.connectivity, kind.background, kind.single_color)
    if isinstance(kind, vocab.ColorLayers):
        return _partition_color_layers(grid)
    if isinstance(kind, vocab.RowSegments):
        return row_segments(grid, kind.background)
    if isinstance(kind, vocab.ColSegments):
        return col_segments(grid, kind.background)
    raise InterpreterError(f"unknown partition kind: {kind!r}")


def _partition_blocks(grid: Grid, h: int, w: int) -> List[RegionValue]:
    rows, cols = grid_dims(grid)
    if rows % h != 0 or cols % w != 0:
        raise InterpreterError(f"blocks({h}, {w}) does not evenly divide {rows}x{cols}")
    result = []
    for r0 in range(0, rows, h):
        for c0 in range(0, cols, w):
            cells = [row[c0 : c0 + w] for row in grid[r0 : r0 + h]]
            result.append(RegionValue(row0=r0, col0=c0, rows=h, cols=w, cells=cells))
    return result


def _partition_objects(
    grid: Grid, connectivity: int, background: int, single_color: bool = True
) -> List[RegionValue]:
    """A second, independent segmentation implementation from
    `perception/objects.py` (RN-CUR-14, object pack Section 3.3): this
    module never imports `perception/`, so the two are compared only by
    an explicit equivalence test on real grids, not by sharing code."""
    rows, cols = grid_dims(grid)
    if connectivity == 4:
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    elif connectivity == 8:
        deltas = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]
    else:
        raise InterpreterError(f"objects(): connectivity must be 4 or 8, got {connectivity}")
    seen = [[False] * cols for _ in range(rows)]
    result = []
    for r0 in range(rows):
        for c0 in range(cols):
            if seen[r0][c0] or grid[r0][c0] == background:
                continue
            component = _flood_fill(grid, seen, r0, c0, background, deltas, single_color)
            rmin = min(r for r, _ in component)
            rmax = max(r for r, _ in component)
            cmin = min(c for _, c in component)
            cmax = max(c for _, c in component)
            cells = [
                [
                    grid[r][c] if (r, c) in component else None
                    for c in range(cmin, cmax + 1)
                ]
                for r in range(rmin, rmax + 1)
            ]
            result.append(
                RegionValue(
                    row0=rmin, col0=cmin, rows=rmax - rmin + 1, cols=cmax - cmin + 1, cells=cells
                )
            )
    return result


def _flood_fill(grid, seen, r0, c0, background, deltas, single_color: bool = True):
    """Grows a component from (r0, c0) over orthogonally/diagonally
    adjacent (per `deltas`) non-background cells. When `single_color` is
    true (object pack Section 3.3's `objects(connectivity, background,
    single_color)`), growth stops at a color change, matching
    `perception/objects.py`'s own color-separated components; when false,
    any touching non-background cell joins regardless of color."""
    rows, cols = grid_dims(grid)
    own_color = grid[r0][c0]
    stack = [(r0, c0)]
    seen[r0][c0] = True
    component = set()
    while stack:
        r, c = stack.pop()
        component.add((r, c))
        for dr, dc in deltas:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not seen[nr][nc]:
                neighbor = grid[nr][nc]
                if neighbor == background:
                    continue
                if single_color and neighbor != own_color:
                    continue
                seen[nr][nc] = True
                stack.append((nr, nc))
    return component


def _partition_color_layers(grid: Grid) -> List[RegionValue]:
    rows, cols = grid_dims(grid)
    colors = sorted({grid[r][c] for r in range(rows) for c in range(cols)})
    layers = []
    for color in colors:
        cells = [[grid[r][c] if grid[r][c] == color else None for c in range(cols)] for r in range(rows)]
        layers.append(RegionValue(row0=0, col0=0, rows=rows, cols=cols, cells=cells))
    return layers


def _exec_correspond(step: vocab.Correspond, env: Environment) -> None:
    list_a = eval_expr(step.list_a, env)
    list_b = eval_expr(step.list_b, env)
    pairs = _correspond(list_a, list_b, step.by)
    env.bound[step.result_name] = pairs
    env.log("correspond", result=step.result_name, value=len(pairs))


def _correspond(list_a, list_b, by: str) -> List[Tuple[Any, Any]]:
    if by == "index":
        return list(zip(list_a, list_b))
    if by == "position":
        by_pos = {(r.row0, r.col0): r for r in list_b}
        return [(a, by_pos[(a.row0, a.col0)]) for a in list_a]
    if by == "color":
        from src.curriculum.spec._expressions import _scalar_color

        by_color = {}
        for b in list_b:
            by_color.setdefault(_scalar_color(b), b)
        return [(a, by_color[_scalar_color(a)]) for a in list_a]
    if by == "size_rank":
        rank_a = sorted(list_a, key=lambda r: r.rows * r.cols)
        rank_b = sorted(list_b, key=lambda r: r.rows * r.cols)
        return list(zip(rank_a, rank_b))
    raise InterpreterError(f"correspond: unknown by={by!r}")


def _exec_for_each(step: vocab.ForEach, env: Environment) -> None:
    items = eval_expr(step.list_ref, env)
    extent = None
    if isinstance(step.list_ref, vocab.Ref):
        extent = env.partition_extents.get(step.list_ref.name)
    env.log("for_each", region=_expr_repr(step.list_ref), value=len(items))
    for item in ordered_items(items, step.order):
        env.bound[step.element_name] = item
        if extent is not None:
            env.active_extents.append(extent)
        try:
            execute_steps(step.body, env)
        finally:
            if extent is not None:
                env.active_extents.pop()


def _exec_test(step: vocab.Test, env: Environment) -> None:
    result = eval_predicate(step.predicate, env)
    env.bound[step.result_name] = result
    env.log("test", condition=result, result=step.result_name)


def _exec_branch(step: vocab.Branch, env: Environment) -> None:
    condition = env.bound[step.condition_name]
    env.log("branch", condition=condition, value="then" if condition else "else")
    execute_steps(step.then_steps if condition else step.else_steps, env)


def _exec_emit(step: vocab.Emit, env: Environment) -> None:
    if env.output_grid is None:
        raise InterpreterError("emit used before shape_out")
    region = resolve_bound_region(step.region, env)
    if region.rows == 0 or region.cols == 0:
        env.log("emit", region={"rows": 0, "cols": 0}, value="empty-skip")
        return
    source_grid, source_desc = _resolve_emit_source(step.source, env, region)
    if grid_dims(source_grid) != (region.rows, region.cols):
        raise InterpreterError(
            f"emit: source shape {grid_dims(source_grid)} does not match "
            f"region shape ({region.rows}, {region.cols})"
        )
    out_rows = len(env.output_grid)
    out_cols = len(env.output_grid[0])
    for dr in range(region.rows):
        for dc in range(region.cols):
            value = source_grid[dr][dc]
            if value is None:
                continue
            r, c = region.row0 + dr, region.col0 + dc
            if not (0 <= r < out_rows and 0 <= c < out_cols):
                raise InterpreterError(
                    f"emit: destination ({r}, {c}) out of bounds for a "
                    f"{out_rows}x{out_cols} output grid"
                )
            env.output_grid[r][c] = value
    env.log(
        "emit",
        region={"row0": region.row0, "col0": region.col0, "rows": region.rows, "cols": region.cols},
        value=source_desc,
    )


def _resolve_emit_source(source: vocab.EmitSource, env: Environment, region: RegionValue):
    if isinstance(source, vocab.Copy):
        value = eval_expr(source.source, env)
        grid = value.cells if isinstance(value, RegionValue) else value
        return grid, "copy"
    if isinstance(source, vocab.Fill):
        color = eval_expr(source.color, env)
        grid = [[color for _ in range(region.cols)] for _ in range(region.rows)]
        return grid, {"fill": color}
    raise InterpreterError(f"unknown emit source: {source!r}")


def _exec_transform(step: vocab.Transform, env: Environment) -> None:
    region = resolve_bound_region(step.region, env)
    step_op = resolve_op_params(step.op, env)
    if isinstance(step_op, vocab.Halo):
        op = step_op
        new_region = halo_region(region, op.color, op.diagonal, op.background, env.output_grid)
    else:
        new_region = _apply_transform(region, step_op)
    if step.result_name is not None:
        env.bound[step.result_name] = new_region
    env.log(
        "transform",
        region={"row0": region.row0, "col0": region.col0, "rows": region.rows, "cols": region.cols},
        result=step.result_name,
        value=_transform_op_repr(step_op),
    )


def _apply_transform(region: RegionValue, op: vocab.TransformOp) -> RegionValue:
    if isinstance(op, vocab.Rotate):
        cells = region.cells
        for _ in range(op.k % 4):
            cells = [list(row) for row in zip(*cells[::-1])]
        rows, cols = grid_dims(cells)
        return RegionValue(row0=region.row0, col0=region.col0, rows=rows, cols=cols, cells=cells)
    if isinstance(op, vocab.Flip):
        if op.axis == "horizontal":
            cells = [row[::-1] for row in region.cells]
        elif op.axis == "vertical":
            cells = region.cells[::-1]
        else:
            raise InterpreterError(f"flip: unknown axis {op.axis!r}")
        return RegionValue(row0=region.row0, col0=region.col0, rows=region.rows, cols=region.cols, cells=cells)
    if isinstance(op, vocab.Transpose):
        cells = [list(row) for row in zip(*region.cells)]
        rows, cols = grid_dims(cells)
        return RegionValue(row0=region.row0, col0=region.col0, rows=rows, cols=cols, cells=cells)
    if isinstance(op, vocab.Recolor):
        cells = [[op.color_map.get(v, v) for v in row] for row in region.cells]
        return RegionValue(row0=region.row0, col0=region.col0, rows=region.rows, cols=region.cols, cells=cells)
    if isinstance(op, vocab.CropToContent):
        return _crop_to_content(region, op.background)
    if isinstance(op, vocab.RecolorObject):
        return _paint_object_cells(region, op.color)
    if isinstance(op, vocab.Erase):
        return _paint_object_cells(region, op.background)
    if isinstance(op, vocab.FillBbox):
        cells = [[op.color for _ in row] for row in region.cells]
        return RegionValue(row0=region.row0, col0=region.col0, rows=region.rows, cols=region.cols, cells=cells)
    if isinstance(op, vocab.RecolorObjectPart):
        return _paint_object_part(region, op.part, op.color)
    if isinstance(op, vocab.FillEnclosed):
        return _fill_enclosed(region, op.color)
    if isinstance(op, vocab.OverlayParts):
        return overlay_parts_region(region, op)
    if isinstance(op, vocab.PanelSummary):
        return summarize_uniform_panels(region, op)
    if isinstance(op, vocab.PanelSwap):
        return swap_panel_masks(region, op)
    if isinstance(op, vocab.Translate):
        return RegionValue(
            row0=region.row0 + op.dr,
            col0=region.col0 + op.dc,
            rows=region.rows,
            cols=region.cols,
            cells=region.cells,
        )
    raise InterpreterError(f"unknown transform op: {op!r}")


def _paint_object_cells(region: RegionValue, color: int) -> RegionValue:
    """Repaints only the region's own object cells (non-None), leaving
    non-member bbox cells (None) untouched - shared by `RecolorObject` and
    `Erase` (object pack Section 3.3), which differ only in the color
    they paint with."""
    cells = [[color if v is not None else None for v in row] for row in region.cells]
    return RegionValue(row0=region.row0, col0=region.col0, rows=region.rows, cols=region.cols, cells=cells)


def _fill_enclosed(region: RegionValue, color: int) -> RegionValue:
    holes = enclosed_positions(region.cells)
    cells = [
        [color if (r, c) in holes else None for c in range(region.cols)]
        for r in range(region.rows)
    ]
    return RegionValue(row0=region.row0, col0=region.col0, rows=region.rows, cols=region.cols, cells=cells)


def _paint_object_part(region: RegionValue, part: str, color: int) -> RegionValue:
    """Repaints only the border or only the interior member cells of the
    region's object (ADR 0081); non-member cells stay None."""
    if part not in ("border", "interior"):
        raise InterpreterError(f"recolor_object_part: unknown part {part!r}")
    interior = interior_positions(region.cells)
    want_interior = part == "interior"
    cells = [
        [
            color if v is not None and ((r, c) in interior) == want_interior else v
            for c, v in enumerate(row)
        ]
        for r, row in enumerate(region.cells)
    ]
    return RegionValue(row0=region.row0, col0=region.col0, rows=region.rows, cols=region.cols, cells=cells)


def _crop_to_content(region: RegionValue, background: int) -> RegionValue:
    positions = [
        (r, c)
        for r in range(region.rows)
        for c in range(region.cols)
        if region.cells[r][c] is not None and region.cells[r][c] != background
    ]
    if not positions:
        raise InterpreterError("crop_to_content: region is entirely background")
    rmin = min(r for r, _ in positions)
    rmax = max(r for r, _ in positions)
    cmin = min(c for _, c in positions)
    cmax = max(c for _, c in positions)
    cells = [row[cmin : cmax + 1] for row in region.cells[rmin : rmax + 1]]
    return RegionValue(
        row0=region.row0 + rmin,
        col0=region.col0 + cmin,
        rows=rmax - rmin + 1,
        cols=cmax - cmin + 1,
        cells=cells,
    )


def _exec_compose(step: vocab.Compose, env: Environment) -> None:
    if env.output_grid is None:
        raise InterpreterError("compose used before shape_out")
    default_color = eval_expr(step.default_color, env)
    for row in env.output_grid:
        for i, cell in enumerate(row):
            if cell is None:
                row[i] = default_color
    env.log("compose", value=default_color)


def _exec_seed(step: vocab.Seed, env: Environment) -> None:
    if env.output_grid is None:
        raise InterpreterError("seed used before shape_out")
    value = eval_expr(step.source, env)
    grid = value.cells if isinstance(value, RegionValue) else value
    rows, cols = grid_dims(grid)
    out_rows = len(env.output_grid)
    out_cols = len(env.output_grid[0])
    if (rows, cols) != (out_rows, out_cols):
        raise InterpreterError(
            f"seed: source shape {(rows, cols)} does not match output "
            f"shape {(out_rows, out_cols)}"
        )
    for r in range(rows):
        for c in range(cols):
            env.output_grid[r][c] = grid[r][c]
    env.log("seed", value="copied")


def _loggable(value: Any) -> Any:
    if isinstance(value, RegionValue):
        return {"row0": value.row0, "col0": value.col0, "rows": value.rows, "cols": value.cols}
    if isinstance(value, list) and value and isinstance(value[0], RegionValue):
        return len(value)
    return value


def _expr_repr(expr: vocab.Expr) -> str:
    if isinstance(expr, vocab.Ref):
        return expr.name
    return repr(expr)


def _transform_op_repr(op: vocab.TransformOp) -> str:
    return type(op).__name__.lower()
