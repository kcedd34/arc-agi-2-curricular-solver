"""Unit tests for _regions.py's SegmentTo resolution (ADR 0066/0067): the
directional scan from a marker cell, stopping according to
`stop_condition`. Covers all 3 stop conditions used by task 4's
`draw_lines` content piece (`same_color_isolated`, `border`,
`any_obstacle`).
"""
import pytest

from src.curriculum.spec import vocabulary as vocab
from src.curriculum.spec._expressions import InterpreterError
from src.curriculum.spec._regions import resolve_bound_region


class _FakeEnv:
    def __init__(self, bound):
        self.bound = bound
        self.output_grid = None
        self.active_extents = []


def _segment(row, col, direction, stop_condition="same_color_isolated"):
    return vocab.SegmentTo(
        grid=vocab.Ref("g"),
        from_row=row,
        from_col=col,
        direction=direction,
        background=0,
        stop_condition=stop_condition,
    )


def test_segment_to_finds_isolated_same_color_partner():
    grid = [
        [0, 0, 0, 0, 0],
        [0, 5, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 5, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    env = _FakeEnv({"g": grid})
    region = resolve_bound_region(_segment(1, 1, "down"), env)
    assert (region.row0, region.col0, region.rows, region.cols) == (2, 1, 1, 1)
    assert region.cells == [[0]]


def test_segment_to_empty_when_no_partner_in_direction():
    grid = [
        [0, 0, 0],
        [0, 5, 0],
        [0, 0, 0],
    ]
    env = _FakeEnv({"g": grid})
    region = resolve_bound_region(_segment(1, 1, "right"), env)
    assert (region.rows, region.cols) == (0, 0)


def test_segment_to_empty_when_blocked_by_non_isolated_same_color_cell():
    grid = [
        [0, 0, 0, 0],
        [0, 5, 0, 0],
        [0, 5, 5, 0],
        [0, 0, 0, 0],
    ]
    env = _FakeEnv({"g": grid})
    region = resolve_bound_region(_segment(1, 1, "down"), env)
    assert (region.rows, region.cols) == (0, 0)


def test_segment_to_out_of_bounds_origin_raises_interpreter_error():
    grid = [[0, 0], [0, 0]]
    env = _FakeEnv({"g": grid})
    with pytest.raises(InterpreterError):
        resolve_bound_region(_segment(5, 5, "down"), env)


def test_segment_to_unknown_stop_condition_raises_value_error():
    grid = [[0, 0], [0, 0]]
    env = _FakeEnv({"g": grid})
    with pytest.raises(ValueError):
        resolve_bound_region(_segment(0, 0, "down", stop_condition="bogus"), env)


# --- stop_condition="border" (task 4, raio_ate_borda) ----------------------


def test_segment_to_border_returns_between_region_when_scan_reaches_edge():
    grid = [
        [0, 0, 0],
        [0, 5, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]
    env = _FakeEnv({"g": grid})
    region = resolve_bound_region(_segment(1, 1, "down", stop_condition="border"), env)
    assert (region.row0, region.col0, region.rows, region.cols) == (2, 1, 2, 1)
    assert region.cells == [[0], [0]]


def test_segment_to_border_is_empty_when_an_obstacle_blocks_the_way():
    grid = [
        [0, 0, 0],
        [0, 5, 0],
        [0, 3, 0],
        [0, 0, 0],
    ]
    env = _FakeEnv({"g": grid})
    region = resolve_bound_region(_segment(1, 1, "down", stop_condition="border"), env)
    assert (region.rows, region.cols) == (0, 0)


def test_segment_to_border_is_empty_when_adjacent_cell_is_already_out_of_bounds():
    grid = [[0, 5]]
    env = _FakeEnv({"g": grid})
    region = resolve_bound_region(_segment(0, 1, "right", stop_condition="border"), env)
    assert (region.rows, region.cols) == (0, 0)


# --- stop_condition="any_obstacle" (task 4, raio_ate_obstaculo) ------------


def test_segment_to_any_obstacle_stops_at_first_non_background_cell():
    grid = [
        [0, 0, 0, 0],
        [0, 5, 0, 3],
        [0, 0, 0, 0],
    ]
    env = _FakeEnv({"g": grid})
    region = resolve_bound_region(_segment(1, 1, "right", stop_condition="any_obstacle"), env)
    assert (region.row0, region.col0, region.rows, region.cols) == (1, 2, 1, 1)
    assert region.cells == [[0]]


def test_segment_to_any_obstacle_ignores_color_and_isolation():
    """Unlike "same_color_isolated", any non-background cell stops the
    scan, even a non-isolated (touching) same-color cell that
    "same_color_isolated" would reject and resolve to empty instead."""
    grid = [
        [0, 5, 0, 0],
        [0, 0, 0, 0],
        [0, 5, 5, 0],
        [0, 0, 0, 0],
    ]
    env = _FakeEnv({"g": grid})

    same_color_region = resolve_bound_region(
        _segment(0, 1, "down", stop_condition="same_color_isolated"), env
    )
    assert (same_color_region.rows, same_color_region.cols) == (0, 0)

    any_obstacle_region = resolve_bound_region(
        _segment(0, 1, "down", stop_condition="any_obstacle"), env
    )
    assert (any_obstacle_region.row0, any_obstacle_region.col0) == (1, 1)
    assert any_obstacle_region.cells == [[0]]


def test_segment_to_any_obstacle_is_empty_when_border_reached_with_no_obstacle():
    grid = [
        [0, 0, 0],
        [0, 5, 0],
        [0, 0, 0],
    ]
    env = _FakeEnv({"g": grid})
    region = resolve_bound_region(_segment(1, 1, "right", stop_condition="any_obstacle"), env)
    assert (region.rows, region.cols) == (0, 0)


# --- SlideTo (object pack Section 3.3, slide(region, direction, stop)) ----


def _obj_region(row0, col0, cells):
    from src.curriculum.spec._region_value import RegionValue

    rows = len(cells)
    cols = len(cells[0]) if rows else 0
    return RegionValue(row0=row0, col0=col0, rows=rows, cols=cols, cells=cells)


def _slide(region, direction, stop, grid="g", background=0):
    return vocab.SlideTo(
        region=region,
        grid=vocab.Ref(grid),
        background=background,
        direction=direction,
        stop=stop,
    )


def test_slide_border_moves_as_far_as_possible_within_bounds():
    grid = [[0] * 5 for _ in range(1)]
    obj = _obj_region(0, 0, [[5]])
    env = _FakeEnv({"g": grid, "o": obj})
    region = resolve_bound_region(_slide(vocab.RegionRef("o"), "right", "border"), env)
    assert (region.row0, region.col0) == (0, 4)
    assert region.cells == [[5]]


def test_slide_contact_stops_before_a_foreign_obstacle():
    grid = [[0, 0, 0, 3, 0]]
    obj = _obj_region(0, 0, [[5]])
    env = _FakeEnv({"g": grid, "o": obj})
    region = resolve_bound_region(_slide(vocab.RegionRef("o"), "right", "contact"), env)
    assert (region.row0, region.col0) == (0, 2)


def test_slide_contact_ignores_own_trail_cells():
    """A wide object sliding must not collide with the cells it is
    vacating (its own pre-slide occupied cells excluded from contact
    detection)."""
    grid = [[5, 5, 5, 0, 0]]
    obj = _obj_region(0, 0, [[5, 5, 5]])
    env = _FakeEnv({"g": grid, "o": obj})
    region = resolve_bound_region(_slide(vocab.RegionRef("o"), "right", "contact"), env)
    assert (region.row0, region.col0) == (0, 2)


def test_slide_contact_does_not_move_when_immediately_blocked():
    grid = [[5, 3, 0]]
    obj = _obj_region(0, 0, [[5]])
    env = _FakeEnv({"g": grid, "o": obj})
    region = resolve_bound_region(_slide(vocab.RegionRef("o"), "right", "contact"), env)
    assert (region.row0, region.col0) == (0, 0)


def test_slide_preserves_object_shape_and_none_mask():
    grid = [[0, 0, 0, 0]]
    obj = _obj_region(0, 0, [[5, None]])
    env = _FakeEnv({"g": grid, "o": obj})
    region = resolve_bound_region(_slide(vocab.RegionRef("o"), "right", "border"), env)
    assert region.cells == [[5, None]]


def test_slide_unknown_direction_raises_value_error():
    grid = [[0, 0]]
    obj = _obj_region(0, 0, [[5]])
    env = _FakeEnv({"g": grid, "o": obj})
    with pytest.raises(ValueError):
        resolve_bound_region(_slide(vocab.RegionRef("o"), "bogus", "border"), env)


def test_slide_unknown_stop_raises_value_error():
    grid = [[0, 0]]
    obj = _obj_region(0, 0, [[5]])
    env = _FakeEnv({"g": grid, "o": obj})
    with pytest.raises(ValueError):
        resolve_bound_region(_slide(vocab.RegionRef("o"), "right", "bogus"), env)


# --- AtOrigin (object pack Section 3.4, crop_content) ----------------------


def test_at_origin_zeroes_position_keeping_shape_and_cells():
    obj = _obj_region(3, 5, [[5, None], [5, 5]])
    env = _FakeEnv({"o": obj})
    region = resolve_bound_region(vocab.AtOrigin(region=vocab.RegionRef("o")), env)
    assert (region.row0, region.col0) == (0, 0)
    assert (region.rows, region.cols) == (2, 2)
    assert region.cells == [[5, None], [5, 5]]


def test_at_origin_is_a_noop_for_a_region_already_at_origin():
    obj = _obj_region(0, 0, [[7]])
    env = _FakeEnv({"o": obj})
    region = resolve_bound_region(vocab.AtOrigin(region=vocab.RegionRef("o")), env)
    assert (region.row0, region.col0) == (0, 0)
    assert region.cells == [[7]]
