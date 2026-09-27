"""Layout pieces (ADR 0064): how the output grid is partitioned/sized
relative to the input.

RN-CUR-33 step 2 (docs/curriculum/tasks/stage-3-prep.md): `block_grid_layout`
used to take an `arrangement` parameter choosing between two `Partition`
kinds (`Cells()` vs a synthetic `IndexGrid()`) depending on whether a
block's content depended on the corresponding input cell (007bbfb7) or
only on the block's own row/col (00576224). That parameter is removed:
the layout piece now only knows the scale factor per axis, always
partitioning a synthetic `IndexGrid(scale_rows, scale_cols)`. Which real
input cell (if any) a block corresponds to, whether by same position or
by block-row/col parity, is a selector concern (`pieces/selector.py`),
not a layout concern; a selector that needs the real input cell now
looks it up explicitly via `vocab.CellAt` at the block's own index,
since `IndexGrid` partition entries carry no real cell content
(interpreter.py's `_partition_grid` placeholders).

This also makes block size an invariant, not a coincidence: since the
R x C arrangement is always `scale_rows x scale_cols` and
`shape_out = in_shape * scale`, each block's own size always equals the
input's own shape (`shape_out / extent = in_shape`), regardless of the
guessed scale value.
"""
from dataclasses import dataclass
from typing import Optional

from src.curriculum.library.pieces.piece_spec import PieceSpec
from src.curriculum.spec import vocabulary as vocab


@dataclass(frozen=True)
class LayoutPlan:
    shape_out: vocab.ShapeOut
    partition: vocab.Partition
    element_name: str
    seed: Optional[vocab.Step] = None


def _scaled_shape_out(input_ref: str, scale_rows: int, scale_cols: int) -> vocab.ShapeOut:
    g_in = vocab.Ref(input_ref)
    return vocab.ShapeOut(
        rows=vocab.BinOp("*", vocab.Attr(g_in, "rows"), scale_rows),
        cols=vocab.BinOp("*", vocab.Attr(g_in, "cols"), scale_cols),
    )


def block_grid_layout(
    input_ref: str,
    scale_rows: int,
    scale_cols: int,
    element_name: str = "block",
) -> LayoutPlan:
    """One R x C block-grid layout over a synthetic index grid, scaled
    `scale_rows x scale_cols` from `input_ref`'s own shape."""
    partition = vocab.Partition(
        source=vocab.Ref(input_ref),
        kind=vocab.IndexGrid(rows=scale_rows, cols=scale_cols),
        result_name="layout_regions",
    )
    return LayoutPlan(
        shape_out=_scaled_shape_out(input_ref, scale_rows, scale_cols),
        partition=partition,
        element_name=element_name,
    )


def identity_canvas_layout(input_ref: str, element_name: str = "cell") -> LayoutPlan:
    """Same-size canvas (`shape_out = in_shape`), seeded as a full copy
    of the input before any selective overwrite (ADR 0066, RN-CUR-31
    exhaustion evidence: no existing layout produces a same-size
    passthrough canvas, `block_grid_layout` always tiles
    `in_shape * scale`). Partitions `Cells()` over the real input, so each
    ForEach element is exactly one input cell at 1:1 granularity, unlike
    `block_grid_layout`'s synthetic `IndexGrid` (always block-granularity).
    Takes no scale parameters: it is always the identity mapping, general
    to any same-size task, not specific to a guessed scale factor."""
    g_in = vocab.Ref(input_ref)
    return LayoutPlan(
        shape_out=vocab.ShapeOut(rows=vocab.Attr(g_in, "rows"), cols=vocab.Attr(g_in, "cols")),
        partition=vocab.Partition(source=g_in, kind=vocab.Cells(), result_name="layout_regions"),
        element_name=element_name,
        seed=vocab.Seed(source=g_in),
    )


LAYOUT_PIECES = {
    "block_grid": PieceSpec("block_grid", ("scale_rows", "scale_cols"), block_grid_layout),
    "identity_canvas": PieceSpec("identity_canvas", (), identity_canvas_layout),
}
