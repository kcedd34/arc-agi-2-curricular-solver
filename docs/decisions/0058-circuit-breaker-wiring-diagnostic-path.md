# 0058 - Circuit breaker wiring through the diagnostic path

## Status

Accepted, implemented and validated on real GPU hardware. Closes a
documentation gap: the code already referenced "ADR 0058" in three
module docstrings before this file existed.

## Context

ADR 0049 built the per-task neural time circuit breaker
(`NEURAL_TASK_CEILING_SECONDS=400.0`, `src/evaluation/task_time_limit.py`)
and wired it into the one code path that mattered for real Kaggle
submissions: `neural_solver.py`'s production `solve_task`/
`_predict_task_with_neural_solver` loop. That wiring is unrelated to
this ADR and stays exactly as ADR 0049 left it.

The ADR 0057 pilot (100-150 tasks, Qwen3-4B-Base cross-task
pretraining) needs its own new diagnostic/pilot scripts to run
per-task, multi-hour work on real GPU hardware, the same risk profile
that motivated ADR 0049's breaker in the first place. But the
diagnostic path those scripts depend on,
`per_attempt_conditional_mitigation_pair_diagnostics.py` (which itself
calls `train_on_task` and the per-attempt generation loop in
`per_attempt_conditional_generation_diagnostics.py`), had no
`TaskTimeLimiter` wiring at all before this change: `train_on_task`
accepted no `limiter` argument, and the per-attempt generation loop
never called `.check()`. A task stuck in a slow TTT step or a runaway
generation attempt inside this diagnostic path had no ceiling, unlike
the already-protected production path.

This ADR documents that gap being closed, since the code doing it was
written and referenced by its own future ADR number before the ADR
itself was written, an ordering slip against Golden Rule 1 now
corrected.

## Decision

Thread an optional `limiter: Optional[TaskTimeLimiter]` parameter
through the diagnostic call chain, mirroring `neural_solver.py`'s own
split of responsibility exactly:

1. **`src/solvers/neural/ttt_trainer.py`'s `train_on_task`**: accepts
   `limiter`, passes it to a `DeadlineTrainerCallback` registered on
   the `Trainer`, so `TaskTimeExceeded` can interrupt an in-progress
   TTT fine-tune mid-training, not only between tasks.
2. **`src/evaluation/per_attempt_conditional_generation_diagnostics.py`'s
   `generate_with_per_attempt_conditional_counts`**: accepts `limiter`,
   calls `limiter.check()` once per attempt inside the sampling loop,
   the same point `generation.py`'s production
   `generate_grid_predictions` checks it.
3. **`src/evaluation/per_attempt_conditional_mitigation_pair_diagnostics.py`'s
   `diagnose_task_with_per_attempt_conditional_mitigation`**: accepts
   `limiter`, passes the same instance into both `train_on_task` (step
   1) and every pair's generation call (step 2, via a `generate_completion`
   closure). `TaskTimeExceeded`, if raised anywhere inside this
   function, is not caught here; it propagates out to the caller.
4. **The caller** (`run_circuit_breaker_smoke.py`, and by extension any
   future pilot script such as ADR 0057's v3 runner) creates one
   `TaskTimeLimiter` per task, calls `.start()`, wraps the diagnostic
   call in `try/except TaskTimeExceeded`, records the abort via
   `TimeLimitAbortTracker.record_abort(task_id)`, and `continue`s to
   the next task. This is the identical shape as
   `neural_solver.solve_task`'s own per-task loop, deliberately kept
   consistent so a future production change to the breaker's calling
   convention does not need a second, divergent design for the
   diagnostic path.

The limiter is optional (`= None`) at every layer: existing diagnostic
scripts that never pass one keep their current unbounded behavior
unchanged, only callers that opt in gain the ceiling.

### Real GPU validation

`run_circuit_breaker_smoke.py` (2-task smoke tier, evaluation split)
was run for real on WSL2-native GPU hardware. Result (2026-09-18):
`0934a4d8` (the smoke tier's actual first alphabetical task, since
`sample_tiers.py` sorts by raw task-id string and `'0'` sorts before
`'1'`; also the known slow outlier from ADR 0028/0049) correctly
aborted at `elapsed=400.07s`, matching its ADR 0049 production history
almost exactly. `135a2760` completed normally in 341.24s, no abort.
Zero unhandled exceptions, exit code 0. This confirms the wiring
described above fires correctly (aborts the slow task) and does not
false-positive (does not abort the normal task) on real hardware, not
just in unit tests.

## Consequences

- Any future diagnostic or pilot script built on
  `diagnose_task_with_per_attempt_conditional_mitigation` (including
  the ADR 0057 pilot's v3 runner) can now bound each task's wall-clock
  cost the same way production already does, a prerequisite for
  running 100-150 tasks unattended on local GPU without risking one
  slow/degenerate task consuming disproportionate time.
- `TaskTimeExceeded` is deliberately left uncaught inside
  `diagnose_task_with_per_attempt_conditional_mitigation` and
  `generate_with_per_attempt_conditional_counts`; only the top-level
  per-task loop catches it. This keeps the abort decision and its
  bookkeeping (`TimeLimitAbortTracker`) in one place, matching
  production, rather than duplicating catch/record logic at every
  layer.
- No change to `neural_solver.py`'s production wiring (ADR 0049), no
  mitigation removed, no advance to a Kaggle round. This is purely an
  extension of already-accepted machinery to a second, previously
  unprotected code path.

## Alternatives considered

- **Give each diagnostic script its own bespoke timeout mechanism
  instead of reusing `TaskTimeLimiter`:** rejected. `TaskTimeLimiter`
  is already implemented, tested, and empirically validated on real
  Kaggle hardware (ADR 0049); a second mechanism would duplicate that
  validation effort for no benefit and risk behaving differently under
  edge cases already handled once.
- **Catch `TaskTimeExceeded` inside
  `diagnose_task_with_per_attempt_conditional_mitigation` itself,
  returning a partial result instead of propagating:** rejected. This
  would need the function to fabricate a well-formed partial result on
  abort, adding complexity to a diagnostic function for a case the
  caller already handles cleanly (skip the task, move on); it would
  also diverge from production's own split of responsibility.
- **Make `limiter` a required argument instead of optional:** rejected.
  Several existing diagnostic scripts and tests call this code path
  without any per-task ceiling and have no reason to need one (fast,
  already-characterized smoke tasks); requiring it everywhere would be
  a needless breaking change with no safety benefit for those callers.

## References

- [ADR 0028 - Timing anomaly and task complexity investigation](0028-timing-anomaly-and-task-complexity-investigation.md)
- [ADR 0032 - Per-attempt conditional no_repeat_ngram_size mitigation](0032-per-attempt-conditional-ngram-mitigation.md)
- [ADR 0049 - Time-budgeted hybrid symbolic+neural submission pipeline](0049-pipeline-hibrido-orcamento-tempo.md) (per-task neural time circuit breaker section)
- [ADR 0056 - Parser leniency fix and 4-failure-mode mitigation for Qwen3-4B-Base](0056-mitigacao-4-modos-qwen3-base.md)
- [ADR 0057 - Sizing a larger-scale cross-task pretraining attempt, Qwen3-4B-Base](0057-dimensionamento-pretreino-v3-qwen3-base.md)
