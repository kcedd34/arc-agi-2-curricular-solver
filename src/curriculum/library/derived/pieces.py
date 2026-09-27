"""Content pieces owned by the derived family (Round 20). Kept out of the
object-pack registry so the object pack's search space does not grow."""
from typing import List

from src.curriculum.library.pieces.piece_spec import PieceSpec
from src.curriculum.spec import vocabulary as vocab

RECOLOR_CLEAR_CORNER_NW = "recolor_clear_corner_nw"


def recolor_clear_corner_nw_content(
    element_name: str, source_ref: str, color: int, clear: int
) -> List[vocab.Step]:
    """Repaints the region's member cells to `color`, then resets the marker
    cell diagonally outside its top-left corner to `clear` (the value the
    cell holds where no marker sits, not the region background)."""
    elem = vocab.RegionRef(element_name)
    recolored = f"{element_name}_recolored"
    return [
        vocab.Transform(region=elem, op=vocab.RecolorObject(color=color), result_name=recolored),
        vocab.Emit(region=elem, source=vocab.Copy(source=vocab.Ref(recolored))),
        vocab.Emit(region=vocab.CornerCell(elem), source=vocab.Fill(color=clear)),
    ]


DERIVED_PIECES = {
    RECOLOR_CLEAR_CORNER_NW: PieceSpec(
        RECOLOR_CLEAR_CORNER_NW, ("color", "clear"), recolor_clear_corner_nw_content
    ),
}
