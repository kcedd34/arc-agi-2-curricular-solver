"""Object-pack content/action pieces (staging, RN-CUR-36, object-pack.md
Section 3.4): what happens to a selected object.

Five of the six pieces (`keep`, `erase_selected`, `recolor_selected`,
`fill_bbox_selected`, `slide_selected`) share `object_selector.py`'s call
site: they run inside a `ForEach`-over-all-objects loop body, as the
`selected_content` list passed to a selector builder, and act on the
loop's own current element (`element_name`), matching
`library/pieces/content.py`'s established shape.

`crop_content` is the one exception: it pairs 1:1 with
`object_layout.crop_to_selected_object_layout`, which finds the target
object *outside* any per-element content slot (Section 3.4's find-then-
crop flow, `object_compose.py`) and binds it under a fixed name
(`selected_ref`, default `"selected"`). It therefore takes no
`element_name`/`source_ref` and must never be passed to a selector's
`selected_content` slot.

Every `Transform` here computes a new region into a fresh bound name
first, then a separate `Emit` writes it back (the same two-step pattern
`pieces/content.py`'s `flip_content` already uses), because `Transform`
never writes to the output grid itself (interpreter.py's `_exec_transform`
only returns a `RegionValue`).
"""
from typing import List

from src.curriculum.library.pieces.piece_spec import PieceSpec
from src.curriculum.spec import vocabulary as vocab


def keep_content(element_name: str, source_ref: str) -> List[vocab.Step]:
    """No-op: leaves the object as whatever the identity-canvas layout's
    `Seed` step already copied from the input. `source_ref` is accepted
    only to keep the uniform `(element_name, source_ref, ...)` signature."""
    return []


def erase_selected_content(element_name: str, source_ref: str, background: int) -> List[vocab.Step]:
    """Repaints the object's own member cells to `background`, leaving the
    rest of the identity canvas (already seeded from the input) untouched."""
    elem_region = vocab.RegionRef(element_name)
    erased_name = f"{element_name}_erased"
    return [
        vocab.Transform(region=elem_region, op=vocab.Erase(background=background), result_name=erased_name),
        vocab.Emit(region=elem_region, source=vocab.Copy(source=vocab.Ref(erased_name))),
    ]


def recolor_selected_content(element_name: str, source_ref: str, color: int) -> List[vocab.Step]:
    """Repaints the object's own member cells to `color` (object pack
    Section 3.5: `color` is inferred from the output colors added across
    train pairs, never fixed here)."""
    elem_region = vocab.RegionRef(element_name)
    recolored_name = f"{element_name}_recolored"
    return [
        vocab.Transform(region=elem_region, op=vocab.RecolorObject(color=color), result_name=recolored_name),
        vocab.Emit(region=elem_region, source=vocab.Copy(source=vocab.Ref(recolored_name))),
    ]


def fill_bbox_selected_content(element_name: str, source_ref: str, color: int) -> List[vocab.Step]:
    """Repaints the object's entire bounding box, including its own
    non-member (background) gaps, to `color`."""
    elem_region = vocab.RegionRef(element_name)
    filled_name = f"{element_name}_filled"
    return [
        vocab.Transform(region=elem_region, op=vocab.FillBbox(color=color), result_name=filled_name),
        vocab.Emit(region=elem_region, source=vocab.Copy(source=vocab.Ref(filled_name))),
    ]


def _recolor_part_steps(element_name: str, part: str, color: int) -> List[vocab.Step]:
    elem_region = vocab.RegionRef(element_name)
    result_name = f"{element_name}_{part}_painted"
    return [
        vocab.Transform(
            region=elem_region, op=vocab.RecolorObjectPart(part=part, color=color), result_name=result_name
        ),
        vocab.Emit(region=elem_region, source=vocab.Copy(source=vocab.Ref(result_name))),
    ]


def recolor_border_selected_content(element_name: str, source_ref: str, color: int) -> List[vocab.Step]:
    """Repaints only the object's border cells (member cells with a
    4-neighbour outside the object) to `color` (ADR 0081)."""
    return _recolor_part_steps(element_name, "border", color)


def recolor_interior_selected_content(element_name: str, source_ref: str, color: int) -> List[vocab.Step]:
    """Repaints only the object's interior cells (member cells fully
    surrounded by members) to `color` (ADR 0081)."""
    return _recolor_part_steps(element_name, "interior", color)


def hollow_selected_content(element_name: str, source_ref: str, background: int) -> List[vocab.Step]:
    """Repaints the object's interior to `background`, leaving only its
    border ring (ADR 0081)."""
    return _recolor_part_steps(element_name, "interior", background)


def peel_selected_content(element_name: str, source_ref: str, background: int) -> List[vocab.Step]:
    """Repaints the object's border ring to `background`, leaving only its
    interior (ADR 0081)."""
    return _recolor_part_steps(element_name, "border", background)


def fill_holes_selected_content(element_name: str, source_ref: str, color: int) -> List[vocab.Step]:
    """Paints only the holes enclosed by the object (non-member cells
    unreachable from outside its bounding box) with `color` (ADR 0082)."""
    elem_region = vocab.RegionRef(element_name)
    result_name = f"{element_name}_holes_filled"
    return [
        vocab.Transform(region=elem_region, op=vocab.FillEnclosed(color=color), result_name=result_name),
        vocab.Emit(region=elem_region, source=vocab.Copy(source=vocab.Ref(result_name))),
    ]


def _halo_steps(element_name: str, color: int, diagonal: bool, background: int) -> List[vocab.Step]:
    result_name = f"{element_name}_halo"
    halo = vocab.Halo(color=color, diagonal=diagonal, background=background)
    return [
        vocab.Transform(region=vocab.RegionRef(element_name), op=halo, result_name=result_name),
        vocab.Emit(region=vocab.RegionRef(result_name), source=vocab.Copy(source=vocab.Ref(result_name))),
    ]


def halo4_selected_content(element_name: str, source_ref: str, color: int, background: int) -> List[vocab.Step]:
    """Paints the 4-adjacent background ring around the object with `color`
    (ADR 0084)."""
    return _halo_steps(element_name, color, False, background)


def halo8_selected_content(element_name: str, source_ref: str, color: int, background: int) -> List[vocab.Step]:
    """Paints the 8-adjacent background ring around the object with `color`
    (ADR 0084)."""
    return _halo_steps(element_name, color, True, background)


def slide_selected_content(
    element_name: str,
    source_ref: str,
    direction: str,
    stop: str,
    background: int,
) -> List[vocab.Step]:
    """Erases the object at its own original position, then re-emits it at
    the position reached by sliding it along `direction` until `stop`
    (object pack Section 3.3's `slide`), using `source_ref` (the
    unmodified input) as the collision scene so the slide's own contact
    check sees the rest of the input's objects rather than this object's
    own just-erased trail."""
    elem_region = vocab.RegionRef(element_name)
    erased_name = f"{element_name}_erased"
    return [
        vocab.Transform(region=elem_region, op=vocab.Erase(background=background), result_name=erased_name),
        vocab.Emit(region=elem_region, source=vocab.Copy(source=vocab.Ref(erased_name))),
        vocab.Emit(
            region=vocab.SlideTo(
                region=elem_region,
                grid=vocab.Ref(source_ref),
                background=background,
                direction=direction,
                stop=stop,
            ),
            source=vocab.Copy(source=vocab.Ref(element_name)),
        ),
    ]


def crop_content(selected_ref: str = "selected") -> List[vocab.Step]:
    """Emits the object bound under `selected_ref` at the origin of the
    crop layout's own canvas (`AtOrigin`, sized exactly to that object's
    bounding box by `object_compose.py`). Not called with an
    `element_name`/`source_ref`: it runs once, after selection, not once
    per `ForEach` element."""
    return [
        vocab.Emit(
            region=vocab.AtOrigin(region=vocab.RegionRef(selected_ref)),
            source=vocab.Copy(source=vocab.Ref(selected_ref)),
        ),
    ]


CONTENT_PIECES = {
    "keep": PieceSpec("keep", (), keep_content),
    "erase_selected": PieceSpec("erase_selected", ("background",), erase_selected_content),
    "recolor_selected": PieceSpec("recolor_selected", ("color",), recolor_selected_content),
    "fill_bbox_selected": PieceSpec("fill_bbox_selected", ("color",), fill_bbox_selected_content),
    "slide_selected": PieceSpec("slide_selected", ("direction", "stop", "background"), slide_selected_content),
    "recolor_border_selected": PieceSpec("recolor_border_selected", ("color",), recolor_border_selected_content),
    "recolor_interior_selected": PieceSpec(
        "recolor_interior_selected", ("color",), recolor_interior_selected_content
    ),
    "hollow_selected": PieceSpec("hollow_selected", ("background",), hollow_selected_content),
    "peel_selected": PieceSpec("peel_selected", ("background",), peel_selected_content),
    "fill_holes_selected": PieceSpec("fill_holes_selected", ("color",), fill_holes_selected_content),
    "halo4_selected": PieceSpec("halo4_selected", ("color", "background"), halo4_selected_content),
    "halo8_selected": PieceSpec("halo8_selected", ("color", "background"), halo8_selected_content),
    "crop_content": PieceSpec("crop_content", (), crop_content),
}
