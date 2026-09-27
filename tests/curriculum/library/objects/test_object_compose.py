"""Integration tests for the object-pack composition scaffold (staging,
RN-CUR-36, object-pack.md Section 3.4): runs assembled layout+selector+
content step sequences through the real interpreter on small synthetic
grids, proving the pieces genuinely compose, not just that each is
correct in isolation.

Covers object-pack.md Section 3.4's explicit synthetic-test requirement:
a tie case (test_largest_object_tie_selects_nothing, RN-CUR-14), a
non-zero background (test_erase_selected_on_non_zero_background), and a
multicolor object (test_unique_color_object_rejects_a_multicolor_object).
"""
from src.curriculum.library.objects import object_compose
from src.curriculum.spec import interpreter


def test_recolor_selected_largest_object_leaves_others_unchanged():
    grid = [
        [0, 0, 0, 0, 0],
        [0, 5, 5, 0, 0],
        [0, 5, 5, 0, 0],
        [0, 0, 0, 3, 0],
        [0, 0, 0, 0, 0],
    ]
    from src.curriculum.library.objects import object_content

    steps = object_compose.build_identity_canvas_composition(
        input_ref="g_in",
        connectivity=4,
        background=0,
        selector_name="largest_object",
        selected_content=object_content.recolor_selected_content("obj", "g_in", color=9),
    )
    output_grid, _ = interpreter.run(steps, grid)
    assert output_grid == [
        [0, 0, 0, 0, 0],
        [0, 9, 9, 0, 0],
        [0, 9, 9, 0, 0],
        [0, 0, 0, 3, 0],
        [0, 0, 0, 0, 0],
    ]


def test_largest_object_tie_selects_nothing():
    """Two objects of equal size: IsLargest is false for both (RN-CUR-14),
    so recolor_selected never fires and the grid comes back unchanged."""
    from src.curriculum.library.objects import object_content

    grid = [
        [0, 5, 5, 0],
        [0, 0, 0, 0],
        [0, 3, 3, 0],
        [0, 0, 0, 0],
    ]
    steps = object_compose.build_identity_canvas_composition(
        input_ref="g_in",
        connectivity=4,
        background=0,
        selector_name="largest_object",
        selected_content=object_content.recolor_selected_content("obj", "g_in", color=9),
    )
    output_grid, _ = interpreter.run(steps, grid)
    assert output_grid == grid


def test_unique_color_object_rejects_a_multicolor_object():
    """A single_color=False partition can group two colors into one
    connected object; HasUniqueColor must reject it (no single color to
    compare), not guess a dominant color."""
    from src.curriculum.library.objects import object_content

    grid = [
        [0, 0, 0, 0],
        [0, 5, 3, 0],
        [0, 0, 7, 0],
        [0, 0, 0, 0],
    ]
    steps = object_compose.build_identity_canvas_composition(
        input_ref="g_in",
        connectivity=4,
        background=0,
        selector_name="unique_color_object",
        selected_content=object_content.recolor_selected_content("obj", "g_in", color=9),
        single_color=False,
    )
    output_grid, _ = interpreter.run(steps, grid)
    assert output_grid == grid


def test_erase_selected_on_non_zero_background():
    background = 2
    grid = [
        [2, 2, 2, 2],
        [2, 5, 5, 2],
        [2, 5, 5, 2],
        [2, 3, 2, 2],
    ]
    from src.curriculum.library.objects import object_content

    steps = object_compose.build_identity_canvas_composition(
        input_ref="g_in",
        connectivity=4,
        background=background,
        selector_name="objects_of_color",
        selector_params={"color": 5},
        selected_content=object_content.erase_selected_content("obj", "g_in", background=background),
    )
    output_grid, _ = interpreter.run(steps, grid)
    assert output_grid == [
        [2, 2, 2, 2],
        [2, 2, 2, 2],
        [2, 2, 2, 2],
        [2, 3, 2, 2],
    ]


def test_fill_bbox_selected_fills_the_objects_own_holes():
    """An L-shaped object's bounding box includes one non-member cell;
    fill_bbox (unlike erase/recolor) also repaints that hole."""
    from src.curriculum.library.objects import object_content

    grid = [
        [0, 0, 0, 0],
        [0, 5, 5, 0],
        [0, 5, 0, 0],
        [0, 0, 0, 0],
    ]
    steps = object_compose.build_identity_canvas_composition(
        input_ref="g_in",
        connectivity=4,
        background=0,
        selector_name="all_objects",
        selected_content=object_content.fill_bbox_selected_content("obj", "g_in", color=7),
    )
    output_grid, _ = interpreter.run(steps, grid)
    assert output_grid == [
        [0, 0, 0, 0],
        [0, 7, 7, 0],
        [0, 7, 7, 0],
        [0, 0, 0, 0],
    ]


def test_slide_selected_moves_the_object_to_the_border():
    from src.curriculum.library.objects import object_content

    grid = [[5, 0, 0, 0]]
    steps = object_compose.build_identity_canvas_composition(
        input_ref="g_in",
        connectivity=4,
        background=0,
        selector_name="all_objects",
        selected_content=object_content.slide_selected_content(
            "obj", "g_in", direction="right", stop="border", background=0
        ),
    )
    output_grid, _ = interpreter.run(steps, grid)
    assert output_grid == [[0, 0, 0, 5]]


def test_touching_border_and_not_touching_border_select_disjoint_objects():
    from src.curriculum.library.objects import object_content

    grid = [
        [5, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 3, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    touching_steps = object_compose.build_identity_canvas_composition(
        input_ref="g_in",
        connectivity=4,
        background=0,
        selector_name="objects_touching_border",
        selected_content=object_content.recolor_selected_content("obj", "g_in", color=9),
    )
    not_touching_steps = object_compose.build_identity_canvas_composition(
        input_ref="g_in",
        connectivity=4,
        background=0,
        selector_name="objects_not_touching_border",
        selected_content=object_content.recolor_selected_content("obj", "g_in", color=9),
    )
    touching_output, _ = interpreter.run(touching_steps, grid)
    not_touching_output, _ = interpreter.run(not_touching_steps, grid)
    assert touching_output[0][0] == 9 and touching_output[2][2] == 3
    assert not_touching_output[2][2] == 9 and not_touching_output[0][0] == 5


def test_crop_to_selected_object_crops_the_largest_object_to_the_origin():
    grid = [
        [0, 0, 0, 0, 0],
        [0, 3, 0, 0, 0],
        [0, 0, 0, 5, 0],
        [0, 0, 0, 5, 5],
        [0, 0, 0, 0, 0],
    ]
    steps = object_compose.build_crop_composition(
        input_ref="g_in",
        connectivity=4,
        background=0,
        selector_name="largest_object",
    )
    output_grid, _ = interpreter.run(steps, grid)
    assert output_grid == [
        [5, 0],
        [5, 5],
    ]
