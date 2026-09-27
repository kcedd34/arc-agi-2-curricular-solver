"""Selector pieces (ADR 0064, RN-CUR-33 step 2): which blocks get which
content, expressed as a ForEach loop body built around caller-supplied
selected/not-selected content pieces.

Since `block_grid_layout` (`pieces/layout.py`) now always partitions a
synthetic `IndexGrid`, its loop element carries no real input-cell color
(interpreter.py's `_partition_grid` placeholders); a selector that needs
the real input cell looks it up explicitly at the block's own (row, col)
index via `vocab.CellAt`, rather than reading the loop element itself.
"""
from typing import List

from src.curriculum.library.pieces.piece_spec import PieceSpec
from src.curriculum.spec import vocabulary as vocab

_PARITY_MODULUS = 2  # even/odd split: row % _PARITY_MODULUS


def input_cell_not_background_selected_body(
    element_name: str,
    background: int,
    selected_content: List[vocab.Step],
    not_selected_content: List[vocab.Step],
    input_ref: str = "g_in",
) -> List[vocab.Step]:
    """Blocks whose same-position input cell is non-background get
    `selected_content`; background-cell blocks get `not_selected_content`
    (007bbfb7's selector)."""
    elem = vocab.Ref(element_name)
    cell_value = vocab.CellAt(
        grid=vocab.Ref(input_ref), row=vocab.Attr(elem, "row"), col=vocab.Attr(elem, "col")
    )
    return [
        vocab.Test(
            predicate=vocab.IsBackground(value=cell_value, background=background),
            result_name="elem_is_bg",
        ),
        vocab.Branch(
            condition_name="elem_is_bg",
            then_steps=list(not_selected_content),
            else_steps=list(selected_content),
        ),
    ]


def row_parity_selected_body(
    element_name: str,
    selected_content: List[vocab.Step],
    not_selected_content: List[vocab.Step],
) -> List[vocab.Step]:
    """Blocks whose own row index is even get `selected_content`, odd rows
    get `not_selected_content` (00576224's selector)."""
    elem = vocab.Ref(element_name)
    return [
        vocab.Test(
            predicate=vocab.ColorEq(a=vocab.BinOp("%", vocab.Attr(elem, "row"), _PARITY_MODULUS), b=0),
            result_name="row_is_even",
        ),
        vocab.Branch(
            condition_name="row_is_even",
            then_steps=list(selected_content),
            else_steps=list(not_selected_content),
        ),
    ]


def isolated_point_selected_body(
    element_name: str,
    background: int,
    selected_content: List[vocab.Step],
    not_selected_content: List[vocab.Step],
    input_ref: str = "g_in",
) -> List[vocab.Step]:
    """Cells that are non-background and orthogonally isolated (no
    same-colored 4-neighbor) get `selected_content`; every other cell
    gets `not_selected_content` (ded97339's selector, ADR 0066). Only
    meaningful paired with `identity_canvas_layout`'s per-cell `Cells()`
    partition, where the loop element's own (row, col) is a real input
    coordinate; `search/compose.py::_selector_eligible` restricts this
    pairing."""
    elem = vocab.Ref(element_name)
    return [
        vocab.Test(
            predicate=vocab.IsIsolated(
                grid=vocab.Ref(input_ref),
                row=vocab.Attr(elem, "row"),
                col=vocab.Attr(elem, "col"),
                background=background,
            ),
            result_name="elem_is_isolated",
        ),
        vocab.Branch(
            condition_name="elem_is_isolated",
            then_steps=list(selected_content),
            else_steps=list(not_selected_content),
        ),
    ]


SELECTOR_PIECES = {
    "input_cell_not_background": PieceSpec(
        "input_cell_not_background", ("background",), input_cell_not_background_selected_body
    ),
    "row_parity": PieceSpec("row_parity", (), row_parity_selected_body),
    "isolated_point": PieceSpec("isolated_point", ("background",), isolated_point_selected_body),
}
