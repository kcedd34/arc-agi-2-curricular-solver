"""Shared textual marker for the hallucinated-second-example failure mode
(docs/decisions/0028-timing-anomaly-and-task-complexity-investigation.md): a
completion never legitimately contains this marker, since a valid answer is
pure digit rows, so its presence means the model kept generating past its
answer into a fabricated second Input:/Output: example.

Split out of generation.py so failure_mode_diagnostics.py (a dependency of
conditional_mitigation.py) does not need to import generation.py, which
would create a generation.py -> conditional_mitigation.py ->
failure_mode_diagnostics.py -> generation.py import cycle once
generation.py itself needs conditional_mitigation.py (ADR 0032
reactivation).
"""

SECOND_EXAMPLE_MARKER = "\nInput:"

__all__ = ["SECOND_EXAMPLE_MARKER"]
