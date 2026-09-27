"""Structural tests for the object-pack layout pieces (staging, RN-CUR-36,
object-pack.md Section 3.4). Full input-to-output behavior is covered by
the integration tests in test_object_compose.py; these check the plans
themselves, since `crop_to_selected_object`'s deferred `shape_out` is a
detail easy to regress silently.
"""
from src.curriculum.library.objects.object_layout import (
    LAYOUT_PIECES,
    crop_to_selected_object_layout,
    identity_canvas_object_layout,
)
from src.curriculum.spec import vocabulary as vocab


def test_layout_pieces_registry_has_both_layouts():
    assert set(LAYOUT_PIECES) == {"identity_canvas", "crop_to_selected_object"}


def test_identity_canvas_layout_has_full_same_size_plan():
    plan = identity_canvas_object_layout("g_in", connectivity=4, background=0)
    assert isinstance(plan.shape_out, vocab.ShapeOut)
    assert isinstance(plan.seed, vocab.Seed)
    assert isinstance(plan.partition.kind, vocab.Objects)
    assert plan.partition.kind == vocab.Objects(connectivity=4, background=0, single_color=True)
    assert plan.needs_selection_first is False
    assert plan.element_name == "obj"


def test_crop_layout_defers_shape_out_and_seed():
    plan = crop_to_selected_object_layout("g_in", connectivity=8, background=2, single_color=False)
    assert plan.shape_out is None
    assert plan.seed is None
    assert plan.partition.kind == vocab.Objects(connectivity=8, background=2, single_color=False)
    assert plan.needs_selection_first is True


def test_both_layouts_partition_the_same_input_ref():
    identity_plan = identity_canvas_object_layout("g_in", connectivity=4, background=0)
    crop_plan = crop_to_selected_object_layout("g_in", connectivity=4, background=0)
    assert identity_plan.partition.source == vocab.Ref("g_in")
    assert crop_plan.partition.source == vocab.Ref("g_in")
