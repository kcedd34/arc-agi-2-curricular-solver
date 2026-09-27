# 0033 - Consolidated current config, pre-validation

## Status

Accepted, but scoped explicitly: "Accepted" here means "current default
configuration to keep developing against", not "final production
configuration for the submission pipeline". That larger decision is out
of scope for this ADR and can only be made after a `validation`-tier run
(Golden Rule 7), see [ADR 0034](0034-first-validation-consolidated-config.md).

## Context

Three separate, independently sanity-tested findings have accumulated
across the diagnostic chain, each still carrying an Informative status
because none of them individually cleared the `validation`-tier bar
(Golden Rule 7):

1. The deterministic shape constraint (ADR 0025/0026): truncates/pads a
   generated grid to the test input's own shape, gated on
   `output_shape_equals_input_shape(task)` holding across all of a task's
   train pairs. Fixed 8/8 fixable held-out test pairs in the sanity
   sample, no observed downside.
2. `geometric_plus_color` augmentation (ADR 0021/0027): full 8-element D4
   geometric augmentation (already the default) plus 2 color-permutation
   variants per already-augmented train pair, color 0 fixed. Net-positive
   but non-uniform held-out per-cell accuracy on the sanity sample's
   "close" tasks (mean 0.74 to 0.76), at a real TTT-time cost (about 2.8x)
   and a smaller total-wall-time cost (about 1.3x on the 6 tasks
   unaffected by the timing anomaly investigated separately in ADR 0028).
3. The ADR 0032 per-attempt conditional decode escalation policy: every
   generation attempt (not only the first) is checked for ADR 0028's
   degenerate pattern, escalating a pair to `no_repeat_ngram_size=3` as
   soon as any of its attempts shows it, one-way. Resolves the held-out
   accuracy regression the unconditional `ngram_only` config caused on
   unaffected tasks (ADR 0029/0030), and delivers a real timing cut on
   `13e47133` (-65.9%); `0934a4d8`'s timing behavior stayed mixed across
   two sanity-tier runs (ADR 0031: +24% vs. baseline, ADR 0032: +33%),
   attributed to run-to-run TTT/sampling stochasticity rather than a
   design flaw, and treated here as an accepted outlier since `0934a4d8`
   does not score under the current pipeline regardless of decode timing
   (see ADR 0028's structural-outlier framing).

The user's explicit decision: stop re-testing these three pieces in
isolation and combine them into one current working config, so the next
real measurement (a `validation`-tier run) tests the pipeline as it will
actually keep being developed, not three separate hypotheticals.

## Decision

The current default `NeuralSolverConfig` for further development combines
all three pieces:

| Piece | Setting | Source |
|---|---|---|
| Shape constraint | Applied whenever `output_shape_equals_input_shape(task)` holds | ADR 0025/0026 |
| Geometric augmentation | `use_geometric_augmentation=True` (already the default) | ADR 0021 |
| Color augmentation | `use_color_augmentation=True`, `num_color_augmentations_per_pair=2`, color 0 fixed | ADR 0027 |
| Decode escalation | Per-attempt conditional, `enable_conditional_escalation=True` | ADR 0032 |

Concretely, for the `validation`-tier run this ADR sets up
([ADR 0034](0034-first-validation-consolidated-config.md)), the
consolidated config is exactly `color_augmentation_configs.py`'s
`geometric_plus_color` variant, run through
`per_attempt_conditional_mitigation_pair_diagnostics.py`'s
`diagnose_task_with_per_attempt_conditional_mitigation` with
`enable_conditional_escalation=True` - the same diagnostic code path
ADR 0027's and ADR 0032's own sanity numbers came from, so the validation
numbers stay directly comparable to everything measured so far.

No new production wiring into `src/solvers/neural_solver.py` /
`src/evaluation/run_neural.py` (the actual submission-facing `solve_task`
path) is done in this ADR. That path still runs the plain, unmitigated
defaults (`use_color_augmentation=False`,
`use_per_attempt_conditional_escalation` does not exist there yet, no
shape constraint applied). Wiring the validated config into that
production path is a separate, explicit follow-up, only worth doing once
a `validation`-tier result exists to justify it (this ADR's own
"Accepted" status is intentionally scoped to stop short of that).

## Consequences

- New file `src/evaluation/run_validation_consolidated_config.py`: runs
  this exact consolidated config against a `validation`-tier sample
  (`sample_tiers.select_tier_tasks(tasks, "validation")`, default 40
  tasks, stratified by expected output grid size per ADR 0015).
- New file `src/evaluation/validation_run_summary.py`: pure, host-testable
  aggregation over the diagnostic rows (`exact_match_rate`,
  `per_cell_accuracy_distribution` with close/middling/far bands,
  `far_outlier_task_ids`, `project_time_for_task_count`), used to answer
  ADR 0034's four measurement questions. 9 new host tests
  (`tests/test_validation_run_summary.py`).
- No change to `src/solvers/neural/config.py`'s dataclass defaults, and no
  change to the production `solve_task` path. This keeps the distinction
  explicit between "what we are now measuring at validation tier" and
  "what actually ships", per this ADR's scoped Status.
- Full host suite: 166/166 passing (157 prior + 9 new).

## Alternatives considered

- **Flipping `NeuralSolverConfig`'s own defaults (`use_color_augmentation`,
  etc.) to make this the literal production default immediately:**
  rejected for this ADR. The user was explicit that "Accepted" here means
  "current config to keep developing against", and the production
  decision is deliberately deferred to after the `validation`-tier read
  (ADR 0034). Changing the shared dataclass default now would blur that
  distinction and silently change `run_neural.py`'s real behavior before
  that read exists.
- **Re-running the sanity-tier comparisons once more with all three
  pieces combined, before validation:** rejected as redundant; each piece
  already has its own sanity-tier evidence, and Golden Rule 7 says only a
  `validation`-tier result can back a policy decision, so the more
  valuable next step is the real validation run, not another sanity
  round.

## References

- [ADR 0015 - Layered sampling](0015-layered-sampling.md)
- [ADR 0021 - Geometric augmentation smoke test](0021-augmentation-geometric-smoke-test.md)
- [ADR 0025 - Deterministic shape constraint](0025-deterministic-shape-constraint.md)
- [ADR 0026 - Shape constraint at the sanity layer](0026-shape-constraint-sanity.md)
- [ADR 0027 - Color augmentation at the sanity layer](0027-color-augmentation-sanity.md)
- [ADR 0032 - Per-attempt conditional no_repeat_ngram_size mitigation](0032-per-attempt-conditional-ngram-mitigation.md)
