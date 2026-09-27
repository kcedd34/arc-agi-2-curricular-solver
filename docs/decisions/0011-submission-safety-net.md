# 0011 - Submission safety net for empty candidates

**Status:** Accepted (2026-09-07)

## Context

ADR 0008 and ADR 0009 confirmed that, for the current 8-task sample, both
the neural solver and the symbolic baseline can return zero candidate
grids for a test pair. Before that changes, `submission_format.py` already
filled a missing `attempt_1` with a hardcoded single-cell placeholder
(`[[0]]`), which never solves anything and offers no signal a downstream
reviewer could reason about.

## Decision

Add a last-layer fallback, applied only when a solver returns an empty
prediction list for a test pair, at the submission-generation layer
(`src/evaluation/submission_fallback.py`, wired into
`src/evaluation/submission_format.py::_build_attempt_pair`). Neither
`neural_solver.py` nor `baseline_solver.py` is touched - both keep
returning `[]` exactly as before; the fallback only ever sees that empty
result and fills the two final attempts:

- `attempt_1`: a literal copy of the test pair's own input grid (correct
  by construction for identity-transform tasks, never worse than a random
  guess for any other transform).
- `attempt_2`: the task's most common train-demonstration output, if one
  value is clearly repeated (strictly higher count than the runner-up);
  otherwise the same input copy used for `attempt_1`.

When a solver returns at least one candidate for a pair, the fallback
never runs - `attempt_1`/`attempt_2` are built from the solver's own
output exactly as before this change.

## Consequences

- `submission.json` no longer contains the uninformative `[[0]]`
  placeholder; every attempt is now a grid derived from the task itself.
- No change to neural/symbolic solver internals or their test coverage.
- `PLACEHOLDER_GRID` is removed from `submission_format.py` since nothing
  reaches it anymore.
- New tests: `tests/test_submission_fallback.py` (fallback logic in
  isolation) and additions to `tests/test_submission_format.py` covering
  both the "both solvers empty, fallback triggers" and "a prediction
  exists, fallback does not interfere" cases explicitly.
- This does not fix why candidates are empty (ADR 0009, ADR 0010); it
  only guarantees the final submission is never structurally empty.

## Alternatives considered

- Keep `PLACEHOLDER_GRID = [[0]]`: rejected, strictly worse than an input
  copy for identity-transform tasks and carries no information.
- Implement the fallback inside `neural_solver.py`/`baseline_solver.py`:
  rejected per explicit scope - solver internals should keep returning an
  honest empty result; only the final submission layer needs a floor.
- A more elaborate fallback (e.g., partial-transform search): out of
  scope here; this ADR is a safety net, not an accuracy lever.

## References

- [ADR 0006 - Submission format](0006-submission-format.md)
- [ADR 0008 - Error diagnosis, first round](0008-error-diagnosis-first-round.md)
- [ADR 0009 - Empty-candidate diagnosis](0009-empty-candidate-diagnosis.md)
