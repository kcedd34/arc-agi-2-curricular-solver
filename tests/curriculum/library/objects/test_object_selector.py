"""Structural tests for the object-pack selector pieces (staging,
RN-CUR-36, object-pack.md Section 3.4). Checks each builder's returned
step shape and predicate wiring; end-to-end selection behavior (tie
safety, multicolor rejection) is covered by test_object_compose.py.
"""
from src.curriculum.library.objects.object_selector import (
    SELECTOR_PIECES,
    all_objects_selected_body,
    largest_object_selected_body,
    objects_not_touching_border_selected_body,
    objects_of_color_selected_body,
    objects_touching_border_selected_body,
    smallest_object_selected_body,
    unique_color_object_selected_body,
)
from src.curriculum.spec import vocabulary as vocab

_SELECTED = [vocab.Bind(name="picked", value=vocab.Ref("obj"))]
_NOT_SELECTED = [vocab.Bind(name="skipped", value=vocab.Ref("obj"))]


def test_selector_pieces_registry_has_all_eleven():
    assert set(SELECTOR_PIECES) == {
        "largest_object",
        "smallest_object",
        "unique_color_object",
        "objects_of_color",
        "objects_touching_border",
        "objects_not_touching_border",
        "objects_with_interior",
        "objects_without_interior",
        "objects_with_hole",
        "objects_without_hole",
        "all_objects",
    }


def test_largest_object_body_tests_is_largest_then_branches():
    body = largest_object_selected_body("obj", _SELECTED, _NOT_SELECTED)
    test_step, branch_step = body
    assert isinstance(test_step, vocab.Test)
    assert isinstance(test_step.predicate, vocab.IsLargest)
    assert test_step.predicate.region == vocab.RegionRef("obj")
    assert isinstance(branch_step, vocab.Branch)
    assert branch_step.condition_name == test_step.result_name
    assert branch_step.then_steps == _SELECTED
    assert branch_step.else_steps == _NOT_SELECTED


def test_smallest_object_body_uses_is_smallest():
    body = smallest_object_selected_body("obj", _SELECTED, _NOT_SELECTED)
    assert isinstance(body[0].predicate, vocab.IsSmallest)


def test_unique_color_object_body_uses_has_unique_color():
    body = unique_color_object_selected_body("obj", _SELECTED, _NOT_SELECTED)
    assert isinstance(body[0].predicate, vocab.HasUniqueColor)


def test_objects_of_color_body_uses_object_color_eq_with_given_color():
    body = objects_of_color_selected_body("obj", 5, _SELECTED, _NOT_SELECTED)
    assert isinstance(body[0].predicate, vocab.ObjectColorEq)
    assert body[0].predicate.color == 5


def test_objects_touching_border_and_not_touching_border_swap_branches():
    """Same TouchesBorder predicate; not_touching_border only swaps which
    branch gets selected_content vs not_selected_content (RN-CUR-31: no
    new negated predicate needed for a single caller)."""
    touching = objects_touching_border_selected_body("obj", _SELECTED, _NOT_SELECTED)
    not_touching = objects_not_touching_border_selected_body("obj", _SELECTED, _NOT_SELECTED)
    assert touching[0].predicate == not_touching[0].predicate
    assert isinstance(touching[0].predicate, vocab.TouchesBorder)
    assert touching[1].then_steps == _SELECTED
    assert touching[1].else_steps == _NOT_SELECTED
    assert not_touching[1].then_steps == _NOT_SELECTED
    assert not_touching[1].else_steps == _SELECTED


def test_all_objects_body_is_unconditional_selected_content():
    body = all_objects_selected_body("obj", _SELECTED, _NOT_SELECTED)
    assert body == _SELECTED
