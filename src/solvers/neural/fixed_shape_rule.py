"""Detects a second, broader output-shape rule than shape_rule.py's strict
"output shape equals input shape": axis by axis (rows, columns), the
output either tracks the input's own value along that axis (the same
identity relationship ADR 0025 already trusts, so it carries no extra
evidence burden) or is a fixed constant repeated across every train pair.

The constant hypothesis is only accepted when the input's value along
that axis took at least 3 distinct values across train pairs while the
output stayed put. Requiring only 2 distinct values turned out, when
checked against real held-out data, to be too weak a bar: `38007db0`
passes a 2-value check (train columns 19 and 25 both map to output
columns 7) but its own held-out test data falsifies it (one test pair
needs 8 columns, not 7) - with only one pair of differing inputs to
compare, a coincidental match is as likely as a genuine invariant. See
docs/decisions/0038-fixed-output-shape.md, which also documents
`a32d8b75` as a separate counter-example this module guards against
(input columns never varied at all across its 3 train pairs, so "output
columns are always 24" and "output columns are input columns minus 6"
are indistinguishable from zero data points of variation, let alone 3).
"""
from typing import Optional, Tuple

from src.utils.task_loader import Task

AxisRule = Optional[int]  # None means "use the input's own value for this
                          # axis"; an int means "always this constant".
FixedShapeRule = Tuple[AxisRule, AxisRule]


def _shape(grid):
    return (len(grid), len(grid[0]) if grid else 0)


MIN_DISTINCT_INPUTS_FOR_CONSTANT = 3


def _resolve_axis(in_vals, out_vals) -> Tuple[bool, AxisRule]:
    if all(o == i for i, o in zip(in_vals, out_vals)):
        return True, None
    if len(set(out_vals)) == 1 and len(set(in_vals)) >= MIN_DISTINCT_INPUTS_FOR_CONSTANT:
        return True, out_vals[0]
    return False, None


def resolve_fixed_output_shape(task: Task) -> Optional[FixedShapeRule]:
    """Returns a (rows_rule, cols_rule) pair if both axes are unambiguously
    resolved from the task's train pairs, else None. Each axis rule is
    either None (track the input's own value for that axis) or an int
    (always this constant)."""
    in_shapes = [_shape(pair.input) for pair in task.train]
    out_shapes = [_shape(pair.output) for pair in task.train]

    rows_ok, rows_rule = _resolve_axis([s[0] for s in in_shapes], [s[0] for s in out_shapes])
    cols_ok, cols_rule = _resolve_axis([s[1] for s in in_shapes], [s[1] for s in out_shapes])
    if not (rows_ok and cols_ok):
        return None
    return (rows_rule, cols_rule)


def target_shape_for(rule: FixedShapeRule, input_grid) -> Tuple[int, int]:
    """Applies a resolved rule to a concrete input grid, producing the
    (target_rows, target_cols) pair that force_grid_shape expects."""
    rows_rule, cols_rule = rule
    input_rows, input_cols = _shape(input_grid)
    target_rows = input_rows if rows_rule is None else rows_rule
    target_cols = input_cols if cols_rule is None else cols_rule
    return (target_rows, target_cols)
