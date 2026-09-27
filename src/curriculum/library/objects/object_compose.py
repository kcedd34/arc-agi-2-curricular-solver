"""Object-pack composition scaffold (staging, RN-CUR-36, object-pack.md
Section 3.4): assembles one layout + one selector + one content piece
into a runnable step sequence, for both of the object pack's shapes.

- identity-canvas: a same-size copy of the input; the selector's
  Test/Branch chooses `selected_content` vs `not_selected_content`
  (default: an unchanged copy, `keep`) once per object in a single
  ForEach loop, mirroring `search/compose.py`'s own
  `ShapeOut -> Seed -> Partition -> ForEach -> Compose` assembly order.
- crop-to-selected-object: the selector's Branch instead binds the
  chosen object to a fixed name (`SELECTED_REF`) so it survives past the
  end of the ForEach loop; only then can `ShapeOut` be built from that
  object's own bounding box (interpreter.py's step dispatch has no such
  requirement for Bind/Partition/ForEach/Test/Branch, only for
  ShapeOut/Emit/Compose/Seed, which is what makes this ordering legal).

Not wired into `search/compose.py`: ADR 0069 requires staging pieces to
stay out of the main search space (excluded by construction, i.e. by
never being imported from there) until the package is promoted.
"""
from typing import Any, Dict, List, Optional

from src.curriculum.library.objects import object_content, object_layout, object_selector
from src.curriculum.spec import vocabulary as vocab

SELECTED_REF = "selected"


def settle_order(*contents: List[vocab.Step]) -> Optional[str]:
    """Direction of the first `settle` slide in the given content steps
    (ADR 0091): objects then iterate nearest-to-destination first so they
    stack. `None` when no content settles."""
    for steps in contents:
        for step in steps:
            region = getattr(step, "region", None)
            if isinstance(region, vocab.SlideTo) and region.stop == "settle":
                return region.direction
    return None


def build_identity_canvas_composition(
    input_ref: str,
    connectivity: int,
    background: int,
    selector_name: str,
    selected_content: List[vocab.Step],
    not_selected_content: Optional[List[vocab.Step]] = None,
    selector_params: Optional[Dict[str, Any]] = None,
    single_color: bool = True,
    element_name: str = "obj",
) -> List[vocab.Step]:
    """Same-size output; every object in the input's own partition
    receives `selected_content` or `not_selected_content` (defaulting to
    an unchanged copy, `keep`) according to `selector_name`."""
    if not_selected_content is None:
        not_selected_content = object_content.keep_content(element_name, input_ref)
    layout = object_layout.identity_canvas_object_layout(
        input_ref, connectivity, background, single_color, element_name
    )
    selector_builder = object_selector.SELECTOR_PIECES[selector_name].builder
    body = selector_builder(
        element_name,
        selected_content=selected_content,
        not_selected_content=not_selected_content,
        **(selector_params or {}),
    )
    return [
        vocab.Bind(name=input_ref, value=vocab.Ref("input")),
        layout.shape_out,
        layout.seed,
        layout.partition,
        vocab.ForEach(
            list_ref=vocab.Ref(object_layout.OBJECTS_REF),
            body=body,
            element_name=element_name,
            order=settle_order(selected_content, not_selected_content),
        ),
        vocab.Compose(default_color=background),
    ]


def build_crop_composition(
    input_ref: str,
    connectivity: int,
    background: int,
    selector_name: str,
    selector_params: Optional[Dict[str, Any]] = None,
    single_color: bool = True,
    element_name: str = "obj",
) -> List[vocab.Step]:
    """Finds the object `selector_name` selects, binding it to
    `SELECTED_REF`; sizes the output to that object's own bounding box;
    then crops it there (`crop_to_selected_object` paired with
    `crop_content`, object pack Section 3.4). A selector that selects no
    object (e.g. a tie) leaves `SELECTED_REF` unbound, and `ShapeOut`
    raises rather than guessing a canvas size."""
    layout = object_layout.crop_to_selected_object_layout(
        input_ref, connectivity, background, single_color, element_name
    )
    selector_builder = object_selector.SELECTOR_PIECES[selector_name].builder
    bind_selected = [vocab.Bind(name=SELECTED_REF, value=vocab.Ref(element_name))]
    body = selector_builder(
        element_name,
        selected_content=bind_selected,
        not_selected_content=[],
        **(selector_params or {}),
    )
    selected = vocab.Ref(SELECTED_REF)
    return [
        vocab.Bind(name=input_ref, value=vocab.Ref("input")),
        layout.partition,
        vocab.ForEach(list_ref=vocab.Ref(object_layout.OBJECTS_REF), body=body, element_name=element_name),
        vocab.ShapeOut(rows=vocab.Attr(selected, "rows"), cols=vocab.Attr(selected, "cols")),
        *object_content.crop_content(SELECTED_REF),
        vocab.Compose(default_color=background),
    ]
