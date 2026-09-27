# 0034 - First validation-tier run of the consolidated config

## Status

Informative. This is the first `validation`-tier read of the config ADR
0033 assembled (shape constraint + `geometric_plus_color` augmentation +
ADR 0032 per-attempt conditional decode escalation). Per explicit
instruction, this ADR does not decide a final production configuration on
its own, even where the results read favorably - that joint call stays
open for a following decision.

## Context

ADR 0033 consolidated three independently sanity-tested pieces into one
current dev config and set up the first real `validation`-tier run
(30-50 tasks, Golden Rule 7, [ADR 0015](0015-layered-sampling.md)) to
replace n=8 sanity reads with statistically meaningful validation-tier
evidence. Before launching, the estimated per-task cost from the sanity
sample (roughly 200-400s/task under the combined config) was presented to
the user, who authorized the run and executed it directly (the harness's
own permission classifier also declined to launch it autonomously,
consistent with treating a ~3h GPU job as requiring explicit user
execution).

The run used `src/evaluation/run_validation_consolidated_config.py`:
`sample_tiers.select_tier_tasks(all_tasks, "validation", seed=42)` (40
tasks, stratified by expected output grid size), the `geometric_plus_color`
config, and
`per_attempt_conditional_mitigation_pair_diagnostics.diagnose_task_with_per_attempt_conditional_mitigation`
with `enable_conditional_escalation=True` - the exact same diagnostic code
path ADR 0027's and ADR 0032's sanity numbers came from, so these results
stay directly comparable.

The run completed cleanly: 40/40 sampled tasks processed, zero
errors/tracebacks in the full log
(`outputs/diagnostics/validation_consolidated_config_run.log`), 40 saved
per-task diagnostic files, one per sampled task. Sampled tasks did not
include `13e47133` (the sanity-tier's canonical "far" outlier); ADR
0028's other flagged timing task, `0934a4d8`, is present in this sample.

## Decision

No new lever or production adoption is decided here. This ADR only
records the four measurements the user asked for, against this real
40-task validation sample, for the next joint decision to build on.

### 1. Real `exact_match` on the validation sample

`exact_match_rate_test = 0.0000` (0/54 held-out test-pair rows).

This matches every prior read in this diagnostic chain (ADR 0017 onward):
zero held-out exact matches under any config tested so far. But training
pairs do show exact matches, and at a higher rate than the sanity sample:
12 training-pair rows across 8 distinct tasks came back `exact match: yes,
cell acc: 1.00` (`135a2760`, `16de56c4` x3, `28a6681f`, `71e489b6`,
`d59b0160`, `dbff022c`, `dfadab01` x2, `faa9f03d` x2), 0 held-out. This
confirms, at validation scale, the same training-pair-only overfitting
pattern ADR 0027 first observed at n=8 (there: 5 training-pair matches,
0 held-out) - the pattern is not a small-sample artifact.

### 2. Mean `per_cell_accuracy` and its distribution

`per_cell_accuracy_test`: n=54, mean=0.7716, close=23 (42.6%),
middling=9 (16.7%), far=22 (40.7%) (bands: close ≥0.7, far <0.3, per
`validation_run_summary.py`'s `CLOSE_THRESHOLD`/`FAR_THRESHOLD`, chosen to
match ADR 0026's qualitative precedent).

The mean (0.7716) is in line with, and slightly above, the sanity
sample's "close" subset mean (0.74-0.76, ADR 0027). But the distribution
is wide and bimodal, not concentrated near the mean: the close and far
bands are almost the same size (23 vs. 22), with a comparatively thin
middle (9). The mean alone would have overstated how uniformly the
config performs; a task lands close to fully right or badly wrong far
more often than it lands in between.

### 3. Total time, average time per task, and projection for 240 tasks

`total_seconds = 10796.81` (about 3.0 hours for 40 tasks),
`avg_seconds_per_task = 269.92`,
`projected_seconds_240_tasks = 64780.89` (about 18.0 hours, linear
projection via `project_time_for_task_count`).

This updates [ADR 0013](0013-time-budget-240-tasks.md)'s 240-task/12h
Kaggle budget analysis with a real validation-tier measurement instead of
the n=8 sanity-tier rates ADR 0013 had to reason from. At 18.0 hours
unparallelized, the consolidated config exceeds the 12h budget by a
factor of 1.5, worse than ADR 0013's original framing where only the
fastest, accuracy-failure-dominated rate fit even with an assumed 4x
parallel speedup. Applying that same 4x assumption here
(18.0h / 4 ≈ 4.5h) would fit comfortably, but this run did not test
parallelization, so that number is an extrapolation, not a measurement.

Per-task timing also surfaces one new candidate outlier not previously
flagged: `9aaea919` at 638.80s total (TTT 227.79s), about 2.4x the sample
mean, the slowest task in the run, despite an unremarkable accuracy
profile (train/test cell accuracies 0.89-0.93, not in the far list). By
contrast, `0934a4d8` - the task whose timing was mixed and net-slower
than baseline across ADR 0031 (+24%) and ADR 0032 (+33%) - came back at
229.33s total in this run, below the sample average, suggesting the
per-attempt conditional escalation is now controlling its timing
behavior as designed, at least in this sample. Neither observation is
investigated further here; both are recorded as inputs for a future
timing pass, following ADR 0028's precedent of not chasing a timing
anomaly without a dedicated diagnosis.

### 4. Count of tasks showing the `13e47133`-like "far" profile

`far_outlier_tasks` (12/40, 30.0%): `0934a4d8`, `269e22fb`, `38007db0`,
`3a25b0d8`, `45a5af55`, `7b5033c1`, `8698868d`, `898e7135`, `a251c730`,
`a32d8b75`, `bf45cf4b`, `f560132c` (any train-pair
`constrained_best_cell_accuracy` missing or below 0.3, per
`far_outlier_task_ids`).

This rate (30.0%) is materially higher than the sanity sample's 1/8
(12.5%). `13e47133` itself was not part of this validation sample, so
this is a distinct, larger set of far tasks, not a re-confirmation of the
same one. `0934a4d8` (already flagged structurally in ADR 0028) recurs
here as far on its own training data, even though its held-out timing
looked controlled this run (see above) - reinforcing ADR 0028's finding
that its timing and content problems, while related, are not the same
signal. This higher far-task rate strengthens, rather than weakens, the
case for treating [ADR 0022](0022-hypothesis-reformulation-post-augmentation-discovery.md)'s
cross-task pretraining hypothesis (NVARC-style corpus expansion) as worth
real investment: at validation scale, roughly 3 in 10 tasks show a
profile no decode-level or augmentation-level mitigation tested so far
has touched, not a rare, single-task curiosity.

## Consequences

- Real, validation-tier-sized evidence now exists for every quantity ADR
  0013 and ADR 0022 previously had to reason about from n=8 sanity data
  or from no data at all. Both of those ADRs' open questions can be
  revisited with this data in a future decision, but this ADR does not
  reopen or amend either of them itself.
- The training-pair-only exact-match pattern (0 held-out matches across
  54 test rows, 12 training matches across 8 tasks) is now confirmed at
  validation scale, not just at n=8. Any future claim that this config
  "generalizes" needs to reckon with this number directly.
- The wide close/far split in per-cell accuracy (23 vs. 22, thin middle
  of 9) means a single mean accuracy figure is a poor summary of this
  config's behavior; future reporting on this pipeline should keep
  reporting the distribution, not just the mean.
- Two new, unexamined timing candidates are recorded for a future,
  dedicated timing pass (following ADR 0028's method, not repeated here):
  `9aaea919` as a new slow outlier, and `0934a4d8`'s apparently controlled
  timing in this run as a data point that may or may not hold up under
  re-measurement.
- No change to any code, config default, or the production `solve_task`
  path. No production decision is made.

## Alternatives considered

- **Deciding production adoption of the consolidated config now, given
  the favorable mean per-cell accuracy (0.7716):** rejected per explicit
  user instruction - a first validation-tier read, however favorable on
  one axis, does not by itself justify a final production call, and the
  0% held-out exact-match rate and 18h/240-task projection are material
  counter-signals that a single-axis read would have hidden.
- **Investigating the two new timing observations (`9aaea919`,
  `0934a4d8`) in this same ADR:** rejected as scope creep; ADR 0028
  established the precedent that a timing anomaly gets its own dedicated
  diagnosis reusing persisted data, not a same-ADR aside, and one
  validation run does not yet establish whether either observation
  recurs.

## References

- [ADR 0013 - Time budget for 240 tasks](0013-time-budget-240-tasks.md)
- [ADR 0015 - Layered sampling](0015-layered-sampling.md)
- [ADR 0022 - Hypothesis reformulation after the pre-existing-augmentation discovery](0022-hypothesis-reformulation-post-augmentation-discovery.md)
- [ADR 0027 - Color augmentation at the sanity layer](0027-color-augmentation-sanity.md)
- [ADR 0028 - Timing anomaly and task complexity investigation](0028-timing-anomaly-and-task-complexity-investigation.md)
- [ADR 0032 - Per-attempt conditional no_repeat_ngram_size mitigation](0032-per-attempt-conditional-ngram-mitigation.md)
- [ADR 0033 - Consolidated current config, pre-validation](0033-consolidated-current-config.md)
