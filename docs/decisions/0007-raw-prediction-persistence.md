# 0007 - Raw prediction persistence

**Status:** Accepted (2026-09-06)

## Context

`src/evaluation/harness.py` only ever returned an aggregated `EvalResult`
(pass/fail counts). It never saved the actual predicted grids anywhere.

This surfaced as a real cost during the first error-diagnostics run
(see the analysis this ADR was requested alongside): producing a
dimension-match / per-cell-accuracy report for the same 8-task/11-pair
evaluation sample already scored once (accuracy=0.0000) required
re-running the full neural solver (TTT + generation, ~15-20 min/task,
up to ~2.5h for 8 tasks) from scratch, because nothing from the earlier
run was kept except the printed aggregate numbers.

## Decision

`evaluate_solver` and `evaluate_solver_on_directory`
(`src/evaluation/harness.py`) accept an optional `predictions_dir`
argument. When given, each task's raw predicted grids (the same
`List[List[Grid]]` shape the solver returns) are saved as
`{task_id}.json` under that directory via
`src/evaluation/prediction_store.py` (`save_predictions`,
`load_predictions`, `load_all_predictions`), before the aggregate score
is computed.

`run_baseline.py` and `run_neural.py` both pass a `predictions_dir` by
default: `outputs/predictions/{baseline,neural}/{split}/`. `outputs/` is
already gitignored, so cached predictions are never committed.

## Consequences

- A later analysis (error diagnostics, a future ensembling comparison)
  can call `load_predictions`/`load_all_predictions` and reuse a
  completed run's real output instead of re-running inference.
- Every evaluation run now also produces a reusable artifact, not just a
  printed number, at the cost of extra disk I/O per task (negligible
  next to per-task TTT/generation time).
- Existing callers of `evaluate_solver`/`evaluate_solver_on_directory`
  are unaffected: `predictions_dir` defaults to `None` (no persistence),
  so this is purely additive.

## Alternatives considered

| Alternative | Pros | Cons |
|---|---|---|
| Keep aggregating only, re-run the solver whenever raw grids are needed | No new code | Repeats the exact ~2.5h cost every time, as just happened |
| Persist predictions inside `EvalResult` itself (in-memory only) | Simpler API | Doesn't survive across separate process runs (CLI script exits between the scoring run and the later analysis) |
| Dedicated `prediction_store.py` + optional `predictions_dir` param (chosen) | Survives across runs; opt-in, no effect on existing callers; small, single-responsibility file | One more small file to maintain |

## References

- [ADR 0006 - Submission format](0006-submission-format.md) (parallel per-task JSON convention)
