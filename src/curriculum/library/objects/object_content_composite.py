"""Composite object content pieces (ADR 0086, Round 9): two disjoint writes
on the same object, curated rather than enumerated as a cartesian product."""
from typing import List

from src.curriculum.library.objects.object_content import (
    erase_selected_content,
    fill_holes_selected_content,
    halo8_selected_content,
)
from src.curriculum.library.pieces.piece_spec import PieceSpec
from src.curriculum.spec import vocabulary as vocab


def fill_holes_erase_selected_content(
    element_name: str, source_ref: str, color: int, background: int
) -> List[vocab.Step]:
    """Fills the enclosed holes with `color`, then erases the object's own
    cells (fill first: its Emit rewrites the object's cells unchanged)."""
    return fill_holes_selected_content(element_name, source_ref, color) + erase_selected_content(
        element_name, source_ref, background
    )


def fill_holes_halo8_selected_content(
    element_name: str, source_ref: str, halo_color: int, color: int, background: int
) -> List[vocab.Step]:
    """Fills the enclosed holes with `color`, then paints the 8-adjacent
    ring with `halo_color` (the halo only touches background cells, so the
    freshly filled holes are kept)."""
    return fill_holes_selected_content(element_name, source_ref, color) + halo8_selected_content(
        element_name, source_ref, halo_color, background
    )


COMPOSITE_PIECES = {
    "fill_holes_erase_selected": PieceSpec(
        "fill_holes_erase_selected", ("color", "background"), fill_holes_erase_selected_content
    ),
    "fill_holes_halo8_selected": PieceSpec(
        "fill_holes_halo8_selected",
        ("halo_color", "color", "background"),
        fill_holes_halo8_selected_content,
    ),
}
