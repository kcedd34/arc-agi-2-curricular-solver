"""Block-tiling primitive family (ADR 0062's own "Worked example: 007bbfb7").

Reproduces, as a reusable and parametrized builder, the exact step
structure the ADR's worked example specifies and
tests/curriculum/spec/test_interpreter.py already proved correct. The
background color and the two tile-scale factors are parameters, not
hardcoded constants: the real Stage-1 learner must infer all of them from
demonstrations, not have any handed to it (see that test module's own
docstring for the same caveat about background; RN-CUR-30's acceptance
review found `scale` was still hardcoded to 3 and required it fixed
before accepting 007bbfb7, since a fixed scale only reproduces this one
task's own 3x3 geometry, not a genuine general block-tiling rule).

`scale_rows`/`scale_cols` are independent (not a single shared `scale`):
each emitted block is a full copy of the input grid, so the interpreter's
`BlockAt` resolver (`_regions.py`) requires the block's own height/width
(`out_rows/rows_in`, `out_cols/cols_in`) to exactly match the input
grid's own shape, i.e. `scale_rows == rows_in` and `scale_cols == cols_in`
for any successful `Copy`. A single shared scale cannot express this for
a non-square input (e.g. 2x3), so RN-CUR-30's generality review (Item 3.3
of the acceptance review) required splitting the parameter before a
non-square synthetic test could pass.

RN-CUR-33 step 2: this builder is now a thin, self-contained wiring of the
shared layout/selector/content pieces (`library/pieces/`), kept separate
from `search/compose.py`'s generic composition builder so `library/`
never depends on `search/` (established one-way layering: `search/`
depends on `library/`, never the reverse).
"""
from typing import List

from src.curriculum.library.registry import REGISTRY, Primitive
from src.curriculum.library.pieces.content import copy_content, fill_content
from src.curriculum.library.pieces.layout import block_grid_layout
from src.curriculum.library.pieces.selector import input_cell_not_background_selected_body
from src.curriculum.spec import vocabulary as vocab


def build_block_tile_by_background(
    background: int, scale_rows: int, scale_cols: int
) -> List[vocab.Step]:
    bg = background
    layout = block_grid_layout("g_in", scale_rows, scale_cols, element_name="cell")
    body = input_cell_not_background_selected_body(
        element_name=layout.element_name,
        background=bg,
        selected_content=copy_content(layout.element_name, "g_in"),
        not_selected_content=fill_content(layout.element_name, "g_in", bg),
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
        vocab.Compose(default_color=bg),
    ]


REGISTRY.register(
    Primitive(
        name="block_tile_by_background",
        params=("background", "scale_rows", "scale_cols"),
        builder=build_block_tile_by_background,
        description=(
            "RxC block-tile rule: for each input cell, emit a full copy of "
            "the input grid where the cell is non-background, else a "
            "background-filled block of the same size; the background "
            "color and the two independent block-scale factors (rows, "
            "cols) are all search-inferred parameters."
        ),
    )
)
