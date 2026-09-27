"""ADR 0090: memoized region values and the input-partition cache equal a
fresh computation."""
from src.curriculum.spec import interpreter
from src.curriculum.spec import vocabulary as vocab
from src.curriculum.spec._expressions import _has_unique_color, _is_extreme, _object_single_color, _region_true_size
from src.curriculum.spec._list_memo import list_memo
from src.curriculum.spec._region_value import RegionValue

GRID = [
    [0, 5, 5, 0, 3],
    [0, 5, 5, 0, 0],
    [7, 0, 0, 0, 3],
    [7, 7, 0, 0, 0],
]


def _objects():
    return interpreter._partition_objects(GRID, 4, 0, True)


def test_true_size_and_color_are_memoized_and_correct():
    sizes = {_region_true_size(r) for r in _objects()}
    assert sizes == {4, 3, 1}
    region = _objects()[0]
    assert _region_true_size(region) == _region_true_size(region) == 4
    assert region.memo["size"] == 4
    assert _object_single_color(region) == 5 and region.memo["color"] == 5


def test_multicolor_region_color_is_none_and_memoized():
    region = RegionValue(0, 0, 1, 2, [[1, 2]])
    assert _object_single_color(region) is None
    assert "color" in region.memo


class _Env:
    def __init__(self, items, element):
        self.bound = {"objs": items, "obj": element, "input": GRID}
        self.active_extents = []
        self.partition_extents = {}


def test_unique_extreme_matches_original_semantics():
    items = _objects()
    largest = max(items, key=_region_true_size)
    for item in items:
        env = _Env(items, item)
        expect = item is largest
        args = (vocab.RegionRef("obj"), vocab.Ref("objs"), env)
        assert _is_extreme(*args, maximize=True) is expect


def test_tie_for_extreme_selects_nothing():
    items = _objects()
    ones = [r for r in items if _region_true_size(r) == 1]
    assert len(ones) == 2
    for item in ones:
        env = _Env(items, item)
        assert _is_extreme(vocab.RegionRef("obj"), vocab.Ref("objs"), env, maximize=False) is False


def test_unique_color_counts_shared_colors_once():
    items = _objects()
    for item in items:
        env = _Env(items, item)
        color = _object_single_color(item)
        shared = sum(1 for other in items if _object_single_color(other) == color)
        assert _has_unique_color(vocab.RegionRef("obj"), vocab.Ref("objs"), env) is (shared == 1)


def test_list_memo_is_not_aliased_across_lists():
    a, b = [1], [1]
    list_memo(a)["k"] = "a"
    assert "k" not in list_memo(b)


def test_input_partition_is_cached_and_equal_to_a_fresh_partition():
    env = interpreter.Environment(bound={"input": GRID})
    kind = vocab.Objects(connectivity=4, background=0, single_color=True)
    first = interpreter._partition_input_cached(GRID, kind, env)
    second = interpreter._partition_input_cached(GRID, kind, env)
    assert first is second
    assert first == interpreter._partition_grid(GRID, kind)


def test_non_input_grids_are_not_cached():
    env = interpreter.Environment(bound={"input": GRID})
    other = [row[:] for row in GRID]
    kind = vocab.Objects(connectivity=4, background=0, single_color=True)
    first = interpreter._partition_input_cached(other, kind, env)
    second = interpreter._partition_input_cached(other, kind, env)
    assert first is not second and first == second
