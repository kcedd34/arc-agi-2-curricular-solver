"""Object-pack layout pieces (staging, RN-CUR-36, object-pack.md Section
3.4): how the output canvas relates to the input's own object partition.

Distinct from `library/pieces/layout.py`'s `LayoutPlan` (block-grid/cell
canvases): an object-pack layout also carries the `Objects` partition
itself, since every object-pack selector/content piece needs it, and
`crop_to_selected_object` cannot compute its own `shape_out` until a
selector has picked the target object first (its canvas size is the
selected object's own bounding box, not a function of the input's shape
alone) - `needs_selection_first` flags that case for the composition
scaffold (`object_compose.py`).
"""
from dataclasses import dataclass
from typing import Optional

from src.curriculum.library.pieces.piece_spec import PieceSpec
from src.curriculum.spec import vocabulary as vocab

OBJECTS_REF = "objects"


@dataclass(frozen=True)
class ObjectLayoutPlan:
    shape_out: Optional[vocab.ShapeOut]
    seed: Optional[vocab.Step]
    partition: vocab.Partition
    element_name: str
    needs_selection_first: bool = False


def _objects_partition(input_ref: str, connectivity: int, background: int, single_color: bool) -> vocab.Partition:
    return vocab.Partition(
        source=vocab.Ref(input_ref),
        kind=vocab.Objects(connectivity=connectivity, background=background, single_color=single_color),
        result_name=OBJECTS_REF,
    )


def identity_canvas_object_layout(
    input_ref: str,
    connectivity: int,
    background: int,
    single_color: bool = True,
    element_name: str = "obj",
) -> ObjectLayoutPlan:
    """Same-size canvas, seeded as a full copy of the input (object pack
    Section 3.4's `identity_canvas`, reusing `pieces/layout.py`'s same-size
    concept), partitioned into the input's own objects instead of `Cells()`
    so a selector/content pair acts at object granularity."""
    g_in = vocab.Ref(input_ref)
    return ObjectLayoutPlan(
        shape_out=vocab.ShapeOut(rows=vocab.Attr(g_in, "rows"), cols=vocab.Attr(g_in, "cols")),
        seed=vocab.Seed(source=g_in),
        partition=_objects_partition(input_ref, connectivity, background, single_color),
        element_name=element_name,
    )


def crop_to_selected_object_layout(
    input_ref: str,
    connectivity: int,
    background: int,
    single_color: bool = True,
    element_name: str = "obj",
) -> ObjectLayoutPlan:
    """Output shaped as the selected object's own bounding box (object pack
    Section 3.4's `crop_to_selected_object`). `shape_out` is left unset:
    the composition scaffold must run the selector first (binding
    "selected"), then build `ShapeOut` from that bound region's own
    rows/cols, before this layout's canvas can exist."""
    return ObjectLayoutPlan(
        shape_out=None,
        seed=None,
        partition=_objects_partition(input_ref, connectivity, background, single_color),
        element_name=element_name,
        needs_selection_first=True,
    )


LAYOUT_PIECES = {
    "identity_canvas": PieceSpec(
        "identity_canvas", ("connectivity", "background", "single_color"), identity_canvas_object_layout
    ),
    "crop_to_selected_object": PieceSpec(
        "crop_to_selected_object", ("connectivity", "background", "single_color"), crop_to_selected_object_layout
    ),
}
