from src.solvers.neural.fixed_shape_rule import resolve_fixed_output_shape, target_shape_for
from src.utils.task_loader import Pair, Task


def _task(train_pairs):
    return Task(task_id="t", train=train_pairs, test=[])


def _grid(rows, cols, value=1):
    return [[value] * cols for _ in range(rows)]


def test_resolves_a_constant_shape_when_input_varies_and_output_does_not():
    # Mirrors 269e22fb: 5 train pairs, varied input shapes, output always (20, 20).
    task = _task([
        Pair(input=_grid(8, 10), output=_grid(20, 20)),
        Pair(input=_grid(16, 8), output=_grid(20, 20)),
        Pair(input=_grid(10, 10), output=_grid(20, 20)),
        Pair(input=_grid(13, 12), output=_grid(20, 20)),
        Pair(input=_grid(8, 10), output=_grid(20, 20)),
    ])
    assert resolve_fixed_output_shape(task) == (20, 20)


def test_resolves_rows_track_input_and_columns_fixed_with_enough_variation():
    # Same pattern as 38007db0's columns (rows track input, columns held
    # constant), but with 3 distinct input column values instead of 2, so
    # the constant hypothesis clears MIN_DISTINCT_INPUTS_FOR_CONSTANT.
    task = _task([
        Pair(input=_grid(19, 19), output=_grid(19, 7)),
        Pair(input=_grid(19, 25), output=_grid(19, 7)),
        Pair(input=_grid(19, 30), output=_grid(19, 7)),
    ])
    assert resolve_fixed_output_shape(task) == (None, 7)


def test_none_when_only_two_distinct_inputs_back_the_constant_hypothesis():
    # Mirrors 38007db0 exactly: input rows never vary (always 19), input
    # columns take only 2 distinct values (19, 25), output columns stay 7
    # both times. This structurally looks resolvable (2 differing inputs
    # both map to the same output), but empirical validation against
    # 38007db0's own held-out test data showed the "columns always 7"
    # hypothesis is false in general (one held-out pair actually needs 8
    # columns) - 2 data points is too thin to trust a coincidental match
    # over a genuine invariant, so this must stay unresolved.
    task = _task([
        Pair(input=_grid(19, 19), output=_grid(19, 7)),
        Pair(input=_grid(19, 25), output=_grid(19, 7)),
    ])
    assert resolve_fixed_output_shape(task) is None


def test_none_when_input_never_varies_along_a_constant_looking_axis():
    # Mirrors a32d8b75: input shape (20, 30) never varies across any of
    # its 3 train pairs, output is always (20, 24). Rows are trivially
    # explained either way (input tracking or a constant), but columns
    # have two equally consistent hypotheses ("always 24" vs. "input
    # columns minus 6") with no data to distinguish them - real
    # ambiguity, not a resolvable rule.
    task = _task([
        Pair(input=_grid(20, 30), output=_grid(20, 24)),
        Pair(input=_grid(20, 30), output=_grid(20, 24)),
        Pair(input=_grid(20, 30), output=_grid(20, 24)),
    ])
    assert resolve_fixed_output_shape(task) is None


def test_none_when_neither_axis_hypothesis_holds():
    task = _task([
        Pair(input=_grid(5, 5), output=_grid(3, 9)),
        Pair(input=_grid(7, 7), output=_grid(4, 2)),
    ])
    assert resolve_fixed_output_shape(task) is None


def test_target_shape_for_applies_constant_rule_to_a_new_input():
    assert target_shape_for((20, 20), _grid(13, 12)) == (20, 20)


def test_target_shape_for_applies_input_tracking_rule_to_a_new_input():
    assert target_shape_for((None, 7), _grid(19, 30)) == (19, 7)
