"""ADR 0091: `settle` slide stacks objects against already-moved ones."""
import pytest

from src.curriculum.library.objects import object_compose, object_content
from src.curriculum.spec import interpreter
from src.curriculum.spec._for_each_order import ordered_items
from src.curriculum.spec._region_value import RegionValue


def _run(grid, direction, stop):
    steps = object_compose.build_identity_canvas_composition(
        input_ref="g_in",
        connectivity=4,
        background=0,
        selector_name="all_objects",
        selected_content=object_content.slide_selected_content(
            "obj", "g_in", direction=direction, stop=stop, background=0
        ),
    )
    return interpreter.run(steps, grid)[0], steps


def test_settle_stacks_objects_in_gravity_down():
    grid = [
        [1, 0, 0],
        [2, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]
    out, _ = _run(grid, "down", "settle")
    assert out == [[0, 0, 0], [0, 0, 0], [1, 0, 0], [2, 0, 0]]


def test_contact_keeps_the_old_input_scene_behavior():
    grid = [
        [1, 0, 0],
        [2, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]
    out, _ = _run(grid, "down", "contact")
    assert out != [[0, 0, 0], [0, 0, 0], [1, 0, 0], [2, 0, 0]]


def test_settle_stacks_against_wall_left_and_ignores_scan_order():
    grid = [[0, 0, 3, 0, 4]]
    out, _ = _run(grid, "left", "settle")
    assert out == [[3, 4, 0, 0, 0]]


def test_settle_is_blocked_by_a_static_obstacle():
    grid = [
        [1, 0],
        [0, 0],
        [5, 0],
    ]
    steps = object_compose.build_identity_canvas_composition(
        input_ref="g_in",
        connectivity=4,
        background=0,
        selector_name="objects_of_color",
        selected_content=object_content.slide_selected_content(
            "obj", "g_in", direction="down", stop="settle", background=0
        ),
        selector_params={"color": 1},
    )
    out, _ = interpreter.run(steps, grid)
    assert out == [[0, 0], [1, 0], [5, 0]]


def test_order_is_derived_only_from_a_settle_slide():
    settle = object_content.slide_selected_content("obj", "g", "down", "settle", 0)
    contact = object_content.slide_selected_content("obj", "g", "down", "contact", 0)
    assert object_compose.settle_order(settle) == "down"
    assert object_compose.settle_order(contact) is None
    assert object_compose.settle_order(contact, settle) == "down"


def _region(row0, col0, rows=1, cols=1):
    return RegionValue(row0, col0, rows, cols, [[1] * cols for _ in range(rows)])


@pytest.mark.parametrize(
    "order,expected",
    [("down", [2, 1, 0]), ("up", [0, 1, 2]), ("right", [2, 1, 0]), ("left", [0, 1, 2]), (None, [0, 1, 2])],
)
def test_ordered_items_nearest_to_edge_first(order, expected):
    items = [_region(0, 0), _region(1, 1), _region(2, 2)]
    got = [items.index(r) for r in ordered_items(items, order)]
    assert got == expected


def test_ordered_items_is_stable_and_rejects_unknown_order():
    items = [_region(1, 0), _region(1, 5)]
    assert ordered_items(items, "down") == items
    with pytest.raises(ValueError):
        ordered_items(items, "sideways")
