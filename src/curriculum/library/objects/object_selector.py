"""Object-pack selector pieces (staging, RN-CUR-36, object-pack.md Section
3.4): which objects of the input's own partition get `selected_content`
vs `not_selected_content`, expressed as a ForEach loop body, mirroring
`library/pieces/selector.py`'s existing shape (`Test` + `Branch`) but
keyed on object-level predicates (vocabulary v2, `spec/vocabulary.py`)
instead of per-cell/per-block ones.

`objects_not_touching_border` reuses `TouchesBorder` unchanged and only
swaps which branch gets `selected_content` (RN-CUR-31: no new predicate,
no `Not` primitive needed for a single caller). `all_objects` needs no
predicate at all: every object is unconditionally selected.

Ties are never resolved silently (object pack Section 3.2.5, Section 4
rule 4): `IsLargest`/`IsSmallest`/`HasUniqueColor` already return False
for every item on a true tie (spec/_expressions.py), so a tied object
simply falls to `not_selected_content` here, it is never guessed into
`selected_content`.
"""
from typing import List

from src.curriculum.library.pieces.piece_spec import PieceSpec
from src.curriculum.library.objects.object_layout import OBJECTS_REF
from src.curriculum.spec import vocabulary as vocab


def _branch(predicate: vocab.Predicate, selected_content: List[vocab.Step], not_selected_content: List[vocab.Step]) -> List[vocab.Step]:
    return [
        vocab.Test(predicate=predicate, result_name="obj_selected"),
        vocab.Branch(condition_name="obj_selected", then_steps=list(selected_content), else_steps=list(not_selected_content)),
    ]


def largest_object_selected_body(
    element_name: str,
    selected_content: List[vocab.Step],
    not_selected_content: List[vocab.Step],
    objects_ref: str = OBJECTS_REF,
) -> List[vocab.Step]:
    """The unique largest object by true cell count (`IsLargest`); every
    object on a size tie for the maximum falls to `not_selected_content`."""
    predicate = vocab.IsLargest(region=vocab.RegionRef(element_name), list_ref=vocab.Ref(objects_ref))
    return _branch(predicate, selected_content, not_selected_content)


def smallest_object_selected_body(
    element_name: str,
    selected_content: List[vocab.Step],
    not_selected_content: List[vocab.Step],
    objects_ref: str = OBJECTS_REF,
) -> List[vocab.Step]:
    """The unique smallest object by true cell count (`IsSmallest`); a
    size tie for the minimum falls to `not_selected_content`."""
    predicate = vocab.IsSmallest(region=vocab.RegionRef(element_name), list_ref=vocab.Ref(objects_ref))
    return _branch(predicate, selected_content, not_selected_content)


def unique_color_object_selected_body(
    element_name: str,
    selected_content: List[vocab.Step],
    not_selected_content: List[vocab.Step],
    objects_ref: str = OBJECTS_REF,
) -> List[vocab.Step]:
    """The object whose own color no other object in the partition shares
    (`HasUniqueColor`); a multi-color object, or a color shared by more
    than one object, falls to `not_selected_content`."""
    predicate = vocab.HasUniqueColor(region=vocab.RegionRef(element_name), list_ref=vocab.Ref(objects_ref))
    return _branch(predicate, selected_content, not_selected_content)


def objects_of_color_selected_body(
    element_name: str,
    color: int,
    selected_content: List[vocab.Step],
    not_selected_content: List[vocab.Step],
) -> List[vocab.Step]:
    """Every object whose own color equals `color` (`ObjectColorEq`, object
    pack Section 3.5: `color` is inferred from the colors common to every
    train input, never fixed here). A multi-color object never matches."""
    predicate = vocab.ObjectColorEq(region=vocab.RegionRef(element_name), color=color)
    return _branch(predicate, selected_content, not_selected_content)


def objects_touching_border_selected_body(
    element_name: str,
    selected_content: List[vocab.Step],
    not_selected_content: List[vocab.Step],
    input_ref: str = "g_in",
) -> List[vocab.Step]:
    """Every object with at least one cell on the input grid's own border
    (`TouchesBorder`)."""
    predicate = vocab.TouchesBorder(region=vocab.RegionRef(element_name), grid=vocab.Ref(input_ref))
    return _branch(predicate, selected_content, not_selected_content)


def objects_not_touching_border_selected_body(
    element_name: str,
    selected_content: List[vocab.Step],
    not_selected_content: List[vocab.Step],
    input_ref: str = "g_in",
) -> List[vocab.Step]:
    """Every object with no cell on the input grid's own border: the same
    `TouchesBorder` test as `objects_touching_border`, with the two
    branches swapped rather than a new negated predicate."""
    predicate = vocab.TouchesBorder(region=vocab.RegionRef(element_name), grid=vocab.Ref(input_ref))
    return _branch(predicate, not_selected_content, selected_content)


def objects_with_interior_selected_body(
    element_name: str,
    selected_content: List[vocab.Step],
    not_selected_content: List[vocab.Step],
) -> List[vocab.Step]:
    """Every object with at least one interior cell (`HasInterior`, ADR
    0081): thick shapes, not 1-cell-wide lines or rings."""
    predicate = vocab.HasInterior(region=vocab.RegionRef(element_name))
    return _branch(predicate, selected_content, not_selected_content)


def objects_without_interior_selected_body(
    element_name: str,
    selected_content: List[vocab.Step],
    not_selected_content: List[vocab.Step],
) -> List[vocab.Step]:
    """The complement of `objects_with_interior`: the same `HasInterior`
    test with the two branches swapped (no negated predicate)."""
    predicate = vocab.HasInterior(region=vocab.RegionRef(element_name))
    return _branch(predicate, not_selected_content, selected_content)


def objects_with_hole_selected_body(
    element_name: str,
    selected_content: List[vocab.Step],
    not_selected_content: List[vocab.Step],
) -> List[vocab.Step]:
    """Every object that encloses at least one hole (`HasHole`, ADR 0082)."""
    predicate = vocab.HasHole(region=vocab.RegionRef(element_name))
    return _branch(predicate, selected_content, not_selected_content)


def objects_without_hole_selected_body(
    element_name: str,
    selected_content: List[vocab.Step],
    not_selected_content: List[vocab.Step],
) -> List[vocab.Step]:
    """The complement of `objects_with_hole`: same `HasHole` test with the
    two branches swapped."""
    predicate = vocab.HasHole(region=vocab.RegionRef(element_name))
    return _branch(predicate, not_selected_content, selected_content)


def all_objects_selected_body(
    element_name: str,
    selected_content: List[vocab.Step],
    not_selected_content: List[vocab.Step],
) -> List[vocab.Step]:
    """Every object, unconditionally: no predicate to evaluate, so
    `not_selected_content` is never reached (accepted for uniform call
    signature with the other selectors)."""
    return list(selected_content)


SELECTOR_PIECES = {
    "largest_object": PieceSpec("largest_object", (), largest_object_selected_body),
    "smallest_object": PieceSpec("smallest_object", (), smallest_object_selected_body),
    "unique_color_object": PieceSpec("unique_color_object", (), unique_color_object_selected_body),
    "objects_of_color": PieceSpec("objects_of_color", ("color",), objects_of_color_selected_body),
    "objects_touching_border": PieceSpec("objects_touching_border", (), objects_touching_border_selected_body),
    "objects_not_touching_border": PieceSpec(
        "objects_not_touching_border", (), objects_not_touching_border_selected_body
    ),
    "objects_with_interior": PieceSpec("objects_with_interior", (), objects_with_interior_selected_body),
    "objects_without_interior": PieceSpec(
        "objects_without_interior", (), objects_without_interior_selected_body
    ),
    "objects_with_hole": PieceSpec("objects_with_hole", (), objects_with_hole_selected_body),
    "objects_without_hole": PieceSpec("objects_without_hole", (), objects_without_hole_selected_body),
    "all_objects": PieceSpec("all_objects", (), all_objects_selected_body),
}
