# 0017 - Post-EOS-fix sanity diagnosis

Status: Informative

## Context

ADR 0016 cleared GPU memory as a blocker on the worst-case task. Per
Golden Rule 7, the next step was a `sanity`-layer run (8 tasks) of
`run_neural.py` to confirm the ADR 0014 model swap (OLMo-2-1124-7B) and
the ADR 0010 EOS fix work together, before considering any larger
`validation`-layer run.

## Method

Ran `python -m src.evaluation.run_neural evaluation sanity`
(2026-09-07, 8 tasks, 11 test pairs). Inspected both the harness's
printed summary and the per-task raw candidate files under
`outputs/predictions/neural/evaluation/` (ADR 0007), the same data
source ADR 0009 used for its original diagnosis.

## Result

| Metric | Value |
|---|---|
| test_pairs_total | 11 |
| test_pairs_correct | 0 |
| accuracy | 0.0000 |

Per-task TTT loss converged normally on every one of the 8 tasks
(training loss dropping from an initial 0.4-3.5 range down to
0.2-0.9 by the final epoch, 3 epochs each), consistent with ADR 0016.

All 8 raw candidate files (`outputs/predictions/neural/evaluation/*.json`)
hold an empty candidate list per test pair (e.g. `[[]]`,
`[[], []]`), meaning `_passes_self_consistency` in
`src/solvers/neural_solver.py` rejected every task, same as ADR 0009's
pre-fix finding. `solve_task` therefore fell back to the symbolic
baseline for all 11 test pairs (ADR 0001's fallback layer), which is why
final accuracy is 0.0000, not a crash or an empty submission.

This run did not capture fresh raw pre-parsing generation text (the
diagnostic capture ADR 0009/0010 used is a separate, not currently
wired-in path), so it cannot distinguish here whether the model is now
producing validly-parsed but simply wrong grids, or still failing to
parse at all. That distinction is the open question for whichever
diagnostic comes next.

## Decision

No lever is decided here. This is a diagnostic result only, per Golden
Rule 7: a `sanity`-layer run never backs a policy or architecture
decision by itself.

The finding is: the ADR 0010 EOS fix, while it corrected a real,
confirmed bug (no trained stop signal, generation running to
`max_new_tokens` almost every time), was **not sufficient on its own**
to produce a single self-consistent candidate at the sanity tier. The
remaining gap is unmeasured and needs its own diagnosis (re-running the
raw-generation capture during a sanity-tier pass, or inspecting
`_passes_self_consistency`'s rejections directly) before picking a next
lever (synthetic/augmented training data, LoRA hyperparameter tuning, or
ensembling, per CLAUDE.md Section 6).

## Consequences

- No code changes from this ADR, diagnostic only.
- CLAUDE.md Section 6 "Missing" list item about validating the ADR 0010
  fix is now answered (validated, and found insufficient alone), and
  replaced with the open question above.
- A `validation`-layer run is not warranted yet, the same "no candidates
  survive" shape of failure as ADR 0009 needs to be re-diagnosed first,
  not scaled up.

## Alternatives considered

- **Proceed directly to a `validation`-layer run since GPU memory is
  cleared:** rejected, memory being cleared (ADR 0016) says nothing
  about accuracy, and this sanity result shows the accuracy problem
  ADR 0009 identified is still present; scaling up an unresolved failure
  mode only spends more compute for the same diagnostic information.
- **Treat the EOS fix as validated based on ADR 0016's TTT convergence
  alone:** rejected, TTT loss converging is necessary but not
  sufficient, `_passes_self_consistency` still rejects every task.

## References

- [ADR 0007 - Raw prediction persistence](0007-raw-prediction-persistence.md)
- [ADR 0009 - Empty-candidate diagnosis](0009-empty-candidate-diagnosis.md)
- [ADR 0010 - Raw generation inspection](0010-raw-generation-inspection.md)
- [ADR 0014 - OSAID-compliant base model](0014-osaid-compliant-base-model.md)
- [ADR 0015 - Layered sampling](0015-layered-sampling.md)
- [ADR 0016 - GPU memory smoke test](0016-gpu-memory-smoke-test.md)
