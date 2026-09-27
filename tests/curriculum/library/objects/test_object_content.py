"""Structural tests for the object-pack content/action pieces (staging,
RN-CUR-36, object-pack.md Section 3.4). Checks each builder's returned
step shape (Transform op, Emit region/source wiring); full input-to-
output behavior is covered by test_object_compose.py.
"""
from src.curriculum.library.objects.object_content import (
    CONTENT_PIECES,
    crop_content,
    erase_selected_content,
    fill_bbox_selected_content,
    keep_content,
    recolor_selected_content,
    slide_selected_content,
)
from src.curriculum.spec import vocabulary as vocab


def test_content_pieces_registry_has_all_thirteen():
    assert set(CONTENT_PIECES) == {
        "keep",
        "erase_selected",
        "recolor_selected",
        "fill_bbox_selected",
        "slide_selected",
        "recolor_border_selected",
        "recolor_interior_selected",
        "hollow_selected",
        "peel_selected",
        "fill_holes_selected",
        "halo4_selected",
        "halo8_selected",
        "crop_content",
    }


def test_halo_contents_transform_then_emit_the_padded_result_region():
    from src.curriculum.library.objects.object_content import halo4_selected_content, halo8_selected_content

    for builder, diagonal in ((halo4_selected_content, False), (halo8_selected_content, True)):
        transform, emit = builder("obj", "g_in", color=3, background=0)
        assert transform.op == vocab.Halo(color=3, diagonal=diagonal, background=0)
        assert emit.region == vocab.RegionRef(transform.result_name)
        assert emit.source == vocab.Copy(source=vocab.Ref(transform.result_name))


def test_keep_content_is_a_true_no_op():
    assert keep_content("obj", "g_in") == []


def test_erase_selected_transforms_then_emits_back_at_same_region():
    steps = erase_selected_content("obj", "g_in", background=3)
    transform, emit = steps
    assert isinstance(transform, vocab.Transform)
    assert transform.region == vocab.RegionRef("obj")
    assert transform.op == vocab.Erase(background=3)
    assert isinstance(emit, vocab.Emit)
    assert emit.region == vocab.RegionRef("obj")
    assert emit.source == vocab.Copy(source=vocab.Ref(transform.result_name))


def test_recolor_selected_uses_recolor_object_op():
    transform, _ = recolor_selected_content("obj", "g_in", color=7)
    assert transform.op == vocab.RecolorObject(color=7)


def test_fill_bbox_selected_uses_fill_bbox_op():
    transform, _ = fill_bbox_selected_content("obj", "g_in", color=4)
    assert transform.op == vocab.FillBbox(color=4)


def test_slide_selected_erases_then_emits_at_slide_to_region():
    steps = slide_selected_content("obj", "g_in", direction="right", stop="border", background=0)
    erase_transform, erase_emit, slide_emit = steps
    assert erase_transform.op == vocab.Erase(background=0)
    assert erase_emit.region == vocab.RegionRef("obj")
    assert isinstance(slide_emit.region, vocab.SlideTo)
    assert slide_emit.region.region == vocab.RegionRef("obj")
    assert slide_emit.region.grid == vocab.Ref("g_in")
    assert slide_emit.region.direction == "right"
    assert slide_emit.region.stop == "border"
    assert slide_emit.source == vocab.Copy(source=vocab.Ref("obj"))


def test_crop_content_emits_selected_region_at_origin():
    (emit,) = crop_content("selected")
    assert isinstance(emit, vocab.Emit)
    assert emit.region == vocab.AtOrigin(region=vocab.RegionRef("selected"))
    assert emit.source == vocab.Copy(source=vocab.Ref("selected"))


def test_crop_content_defaults_to_the_selected_ref_name():
    assert crop_content() == crop_content("selected")
