"""Detects whether a task's train pairs share a mechanically checkable
output-shape rule, so generation can enforce that shape deterministically
instead of relying on the model's learned EOS timing.

ADR 0024 found the model's EOS emission is inconsistent specifically in
the row-count dimension, even for tasks whose true rule is as simple as
"output shape equals input shape" (5 of the 8 sampled tasks). This module
only recognizes that one rule; other rules (a fixed shape regardless of
input, or a partial derivable rule like "rows follow the input, columns
are fixed") are left for a future extension, not implemented here. See
docs/decisions/0025-deterministic-shape-constraint.md.
"""
from src.utils.task_loader import Task


def _shape(grid):
    return (len(grid), len(grid[0]) if grid else 0)


def output_shape_equals_input_shape(task: Task) -> bool:
    """True only if every train pair's output has the exact same shape
    (row count and column count) as its own input. A single counter-example
    among the train pairs is enough to reject the rule for this task."""
    return all(_shape(pair.output) == _shape(pair.input) for pair in task.train)
