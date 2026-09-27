"""Alternating-mirror block-tiling primitive family (ADR 0064's worked
example: 00576224).

Shares its layout formula (`out = in_shape * scale`) with
`block_tile_by_background`, and partitions the same synthetic `IndexGrid`
(RN-CUR-33 step 2: `block_grid_layout` always does, `arrangement` is
gone), but uses the row-parity selector (`row_parity_selected_body`) in
place of the background test: every block is filled (no background
test), block `(r, c)` is an unchanged copy of the input when `r` is
even (`copy_content`), a horizontally-flipped copy when `r` is odd
(`flip_content`), independent of `c`. See
docs/curriculum/tasks/00576224.md for the RN-CUR-31 exhaustion evidence
establishing that only the layout piece (`IndexGrid`) needed to be new
when this primitive was first built; selector and content both
reuse/compose already-existing pieces.

RN-CUR-33 step 2: this builder is now a thin, self-contained wiring of the
shared layout/selector/content pieces (`library/pieces/`), kept separate
from `search/compose.py`'s generic composition builder so `library/`
never depends on `search/` (established one-way layering: `search/`
depends on `library/`, never the reverse).
"""
from typing import List

from src.curriculum.library.registry import REGISTRY, Primitive
from src.curriculum.library.pieces.content import copy_content, flip_content
from src.curriculum.library.pieces.layout import block_grid_layout
from src.curriculum.library.pieces.selector import row_parity_selected_body
from src.curriculum.spec import vocabulary as vocab


def build_block_tile_alternating_mirror(
    scale_rows: int, scale_cols: int
) -> List[vocab.Step]:
    layout = block_grid_layout("g_in", scale_rows, scale_cols, element_name="block")
    body = row_parity_selected_body(
        element_name=layout.element_name,
        selected_content=copy_content(layout.element_name, "g_in"),
        not_selected_content=flip_content(layout.element_name, "g_in", axis="horizontal"),
    )
    return [
        vocab.Bind(name="g_in", value=vocab.Ref("input")),
        layout.shape_out,
        layout.partition,
        vocab.ForEach(
            list_ref=vocab.Ref(layout.partition.result_name),
            element_name=layout.element_name,
            body=body,
        ),
        vocab.Compose(default_color=0),
    ]


REGISTRY.register(
    Primitive(
        name="block_tile_alternating_mirror",
        params=("scale_rows", "scale_cols"),
        builder=build_block_tile_alternating_mirror,
        description=(
            "RxC block-tile rule over a synthetic index grid (independent of "
            "the input's own shape): every block is filled (no background "
            "test), each block a full copy of the input, horizontally "
            "flipped when the block's own row index is odd, unchanged "
            "otherwise; the two independent block-scale factors (rows, "
            "cols) are search-inferred parameters."
        ),
    )
)
