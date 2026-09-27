"""Content pieces (ADR 0064, RN-CUR-33 step 2): what gets written into a
selected block region.

Every piece emits into the `BlockAt(elem.row, elem.col)` region aligned
with the current ForEach loop element (RegionValue always exposes
row0/col0 under `row`/`col` attrs regardless of which PartitionKind
produced it, so this pattern is layout-independent). Every piece shares
the same `(element_name, source_ref, **params)` call signature so
`search/compose.py` can call any content piece the same way regardless
of whether it actually reads from `source_ref`.
"""
from typing import List

from src.curriculum.library.pieces.piece_spec import PieceSpec
from src.curriculum.spec import vocabulary as vocab


def _block_region(element_name: str) -> vocab.BlockAt:
    elem = vocab.Ref(element_name)
    return vocab.BlockAt(row=vocab.Attr(elem, "row"), col=vocab.Attr(elem, "col"))


def copy_content(element_name: str, source_ref: str) -> List[vocab.Step]:
    """Emit a full copy of `source_ref` into the current block."""
    return [
        vocab.Emit(region=_block_region(element_name), source=vocab.Copy(source=vocab.Ref(source_ref)))
    ]


def fill_content(element_name: str, source_ref: str, fill_color: int) -> List[vocab.Step]:
    """Emit a solid-color block, all cells `fill_color`. `source_ref` is
    accepted only to keep every content piece's call signature uniform;
    this piece does not read from it.

    Named `fill_color`, not `background`, because this is a color the
    piece *writes* into the output (search/pruning.infer_target_color_
    candidates' role), unlike `draw_lines_content`'s/`isolated_point`'s
    `background`, which is a color they *detect* to know where to stop
    (search/pruning.infer_colors_common_to_every_input's role). The two
    roles need different candidate lists, so they need different
    parameter names (search/params.py, RN-CUR-33 step 3 continuation)."""
    return [vocab.Emit(region=_block_region(element_name), source=vocab.Fill(color=fill_color))]


def flip_content(element_name: str, source_ref: str, axis: str = "horizontal") -> List[vocab.Step]:
    """Copy `source_ref` into the block, then flip it along `axis`.
    `Transform` resolves its region's cells from the output grid as
    currently written (`BlockAt`, RN-CUR-27), so the plain copy must be
    emitted first before the flipped version can be computed and
    re-emitted over it (same mechanism the retired `alternating_mirror_
    content` used, RN-CUR-31 exhaustion evidence,
    docs/curriculum/tasks/00576224.md)."""
    region = _block_region(element_name)
    flipped_name = f"{element_name}_flipped"
    return [
        vocab.Emit(region=region, source=vocab.Copy(source=vocab.Ref(source_ref))),
        vocab.Transform(region=region, op=vocab.Flip(axis=axis), result_name=flipped_name),
        vocab.Emit(region=region, source=vocab.Copy(source=vocab.Ref(flipped_name))),
    ]


_DIRECTIONS = ("up", "down", "left", "right")


def draw_lines_content(
    element_name: str,
    source_ref: str,
    background: int,
    stop_condition: str = "same_color_isolated",
) -> List[vocab.Step]:
    """From the current cell (an isolated marker), draw a straight
    same-color segment in each of the 4 directions, stopping according to
    `stop_condition` (ded97339's content, ADR 0066; generalized for task 4,
    ADR 0068, RN-CUR-31):

    - "same_color_isolated": toward an isolated same-color partner sharing
      the marker's row or column (ADR 0066's original `ligar_pontos_mesma_cor`
      behavior).
    - "border": all the way to the grid border (`raio_ate_borda`).
    - "any_obstacle": up to (not including) the first non-background cell
      of any color (`raio_ate_obstaculo`).

    A direction whose `SegmentTo` region does not resolve (e.g. no valid
    partner, or an obstacle in the way of a "border" scan) resolves to
    empty, which `Emit` treats as a no-op (interpreter.py). Does not touch
    the cell's own position: that is already correct from the layout's
    `Seed` step (a copy of the input), so unlike `copy_content`/
    `fill_content` this piece never emits into `BlockAt(element_name)`."""
    elem = vocab.Ref(element_name)
    color = vocab.CellAt(
        grid=vocab.Ref(source_ref), row=vocab.Attr(elem, "row"), col=vocab.Attr(elem, "col")
    )
    return [
        vocab.Emit(
            region=vocab.SegmentTo(
                grid=vocab.Ref(source_ref),
                from_row=vocab.Attr(elem, "row"),
                from_col=vocab.Attr(elem, "col"),
                direction=direction,
                background=background,
                stop_condition=stop_condition,
            ),
            source=vocab.Fill(color=color),
        )
        for direction in _DIRECTIONS
    ]


def keep_content(element_name: str, source_ref: str) -> List[vocab.Step]:
    """No-op: leaves the cell as whatever the layout's `Seed` step already
    wrote (a copy of the input). General beyond this task: any same-size
    composition where non-selected cells stay unchanged from the input
    needs exactly this (ADR 0066)."""
    return []


CONTENT_PIECES = {
    "copy": PieceSpec("copy", (), copy_content),
    "fill": PieceSpec("fill", ("fill_color",), fill_content),
    "flip": PieceSpec("flip", ("axis",), flip_content),
    "draw_lines": PieceSpec("draw_lines", ("background", "stop_condition"), draw_lines_content),
    "keep": PieceSpec("keep", (), keep_content),
}
