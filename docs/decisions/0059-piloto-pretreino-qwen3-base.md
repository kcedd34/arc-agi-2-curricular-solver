# 0059 - Piloto de pré-treino cross-task em escala intermediária, Qwen3-4B-Base

## Status

Informative. Real result, no scaling decision made.

## Context

ADR 0057 sized a 400-600 task cross-task pretraining attempt
(ADR 0022) using a borrowed assumption: OLMo-2's own measured
TTT-to-pretraining penalty ratio (2.26x, ADR 0036), applied to
Qwen3-4B-Base's own measured TTT rate (ADR 0055, n=3 tasks). The
resulting range (roughly 3-5h optimistic to 25-45h pessimistic for
400-600 tasks) was judged too wide, and resting on a cross-model
assumption, to commit to before running 400-600 real tasks.

Per explicit user instruction, this ADR runs an intermediate-scale
pilot first: 120 pretraining tasks / 12 held-out evaluation tasks
(same order of magnitude as ADR 0036/0039's 150/40-task attempts), but
now with every piece of infrastructure the earlier attempts lacked:
checkpointing, a per-task circuit breaker wired through the diagnostic
path (ADR 0058), the corrected parser and 4 failure-mode detectors
(ADR 0056). The goal is to replace the borrowed OLMo-2 penalty with a
real, Qwen3-4B-Base-measured number, and to run the exact paired
comparison design ADR 0039 used (same held-out eval tasks, with and
without the pretrained adapter) at this larger scale.

Script: `src/evaluation/run_cross_task_pretraining_pilot_v3.py`
(`DEFAULT_PRETRAINING_TASK_COUNT=120`, `DEFAULT_EVAL_TASK_COUNT=12`).
Run for real on local WSL2 GPU hardware, 2026-09-18, task id
`b6g1j0xyv`, full log at
`outputs/diagnostics/cross_task_pretraining_pilot_v3/full_pilot_run_log.txt`.
Per-task result JSON persisted under
`outputs/diagnostics/cross_task_pretraining_pilot_v3/{baseline_no_pretraining,warm_started_from_pretraining_v3}/`.
Manifest files confirm the intended split sizes: 120 pretraining
tasks (`pretraining_split_v3.json`), 12 eval tasks
(`eval_subsample_v3.json`).

## Decision

No new lever decided. This ADR reports a measured result and applies
the success/abandonment criteria ADR 0057 pre-registered.

### Pretraining phase

Completed cleanly, zero errors: `train_runtime=15160s` (~4h13min),
4716 steps, 1 epoch, `train_loss=0.3057`.

### Paired evaluation, baseline vs. warm-started

Both scenarios ran the same 12 held-out eval tasks.

| Scenario | exact_match_rate_test | per_cell_accuracy (mean, n) | close/middling/far | ttt_total_seconds | circuit breaker aborts |
|---|---|---|---|---|---|
| `baseline_no_pretraining` | 0.0000 | 0.8291 (n=10) | 4/1/5 | 2144.23s | 3/12: `135a2760`, `4c416de3`, `dfadab01` |
| `warm_started_from_pretraining_v3` | 0.0000 | 0.9269 (n=8) | 3/0/5 | 1393.51s | 5/12: `135a2760`, `4c416de3`, `9bbf930d`, `d59b0160`, `dfadab01` |

Notable asymmetry not captured by the pre-registered success criteria:
the warm-started scenario aborted **more** tasks by the circuit breaker
(5/12, 41.7%) than baseline (3/12, 25%). All 3 baseline aborts recur
identically in warm-started (same task ids), plus 2 new ones
(`9bbf930d`, `d59b0160`) that completed normally under baseline. This
means the warm-started scenario's own reported metrics (`exact_match`,
`per_cell_accuracy`) are computed over a smaller and different set of
surviving tasks (n=8 test pairs) than baseline's (n=10), a real
comparability caveat: part of the apparent per-cell accuracy gain could
reflect an easier surviving subset, not a true per-task improvement.

### Real penalty measurement (`pretraining_penalty_measurement.py`)

- `pretraining_s_per_example_epoch = 1.6087`
- `mean_ttt_s_per_example_epoch = 0.5103`
- `real_penalty_ratio = 3.1522`

This replaces ADR 0057's borrowed OLMo-2 assumption (2.26x) with a
real, same-model measurement. The real ratio is **worse** (higher) than
the borrowed one: pretraining is relatively more expensive per
example-epoch, versus TTT, on Qwen3-4B-Base at this scale than the
OLMo-2 figure implied.

### Recalculated time estimate for 400-600 tasks

| task_count | optimistic_hours | pessimistic_hours |
|---|---|---|
| 400 | 18.91 | 84.21 |
| 600 | 28.37 | 126.31 |

Compared to ADR 0057's borrowed range (3-5h optimistic, 25-45h
pessimistic), the real measured range is substantially worse at both
ends: the new *optimistic* case for 400 tasks (18.91h) already exceeds
the old *pessimistic* range's lower bound (25h) by a smaller margin
than expected, and the new pessimistic case (84.21-126.31h) is 2-3x the
old pessimistic ceiling. The wide range ADR 0057 flagged as
too-uncertain-to-trust has narrowed in the sense that it is no longer a
cross-model guess, but the real number it resolved to is worse than
either edge of the original borrowed range.

### Success criteria verdict (`evaluate_success_criteria`)

```
has_real_exact_match=False
per_cell_accuracy_gain=0.0978
exceeds_noise_floor_by_multiple=True
parse_failure_delta=0
should_scale=True
```

The per-cell accuracy gain (0.0978) is about 17.4x ADR 0039's measured
noise floor (0.0056), comfortably past the pre-registered 3x
threshold. By the letter of ADR 0057's pre-registered formula, this
triggers `should_scale=True`.

## Consequences

This is a genuinely mixed result, not a clean "scale" or "abandon"
signal:

- **In favor of scaling:** the per-cell accuracy gain clears the
  pre-registered noise-floor bar by a wide margin, the pretraining
  phase itself runs mechanically clean at 120-task scale (checkpointing,
  disjoint split, 4-hour pretraining time all behave as expected), and
  no new parse-failure regression appeared (`parse_failure_delta=0`).
- **Against scaling:**
  - No real held-out `exact_match` in either scenario (0/10 and 0/8
    test pairs respectively) - the accuracy gain is a per-cell
    accuracy improvement only, not evidence of the model getting any
    held-out task fully right.
  - The warm-started scenario's per-cell accuracy is measured over a
    smaller, different, and by construction "easier" surviving subset
    (7 completed tasks vs. baseline's 9), since it lost 2 more tasks
    to the circuit breaker than baseline did. This is a real
    comparability confound the pre-registered formula does not
    account for; the reported +0.0978 gain should be read with this
    caveat, not taken as a clean like-for-like measurement.
  - The warm-started scenario aborted more tasks overall (5/12 vs.
    3/12), a real degradation on a dimension the success criteria
    never measured. Warm-starting from the pretrained adapter did not
    make evaluation-time TTT faster or more reliable; if anything, two
    additional tasks became slow enough to hit the 400s ceiling.
  - The real, same-model-measured time cost for 400-600 tasks
    (18.91-126.31h) is substantially worse than ADR 0057's already-wide
    borrowed range, confirming that the "lighter model, faster
    pretraining" premise this whole investigation started from
    (ADR 0057) does not hold: Qwen3-4B-Base's pretraining is
    relatively *more* expensive per example-epoch versus its own TTT
    rate than OLMo-2's was.

Per the user's explicit standing instruction, this result is not acted
on unilaterally: no code was changed for this decision, no scaling to
400-600 tasks was started, and no Kaggle action was taken. The combined
result (formal `should_scale=True` verdict, but with two real,
unaccounted-for caveats - the comparability confound and the
circuit-breaker abort asymmetry - plus a substantially worse real time
cost than the original borrowed estimate) is reported for the user's
own joint decision on whether to scale, retry at this same scale with a
fix for the abort-count asymmetry, or treat ADR 0057's abandonment
criteria as effectively met given the real time cost.

## Controlled reanalysis, paired on the intersection of survivors (2026-09-18)

The original paired comparison above is confounded: baseline and
warm-started aborted **different** tasks by the circuit breaker
(baseline 3/12, warm-started 5/12), so each scenario's reported
`per_cell_accuracy` was computed over a different, non-identical subset
of the 12 nominal eval tasks. Per explicit user request, this section
recalculates both scenarios' `per_cell_accuracy` restricted to the
**intersection** of tasks that survived in both scenarios, using only
already-persisted data from this same pilot run (`b6g1j0xyv`), no new
GPU run. Script:
`outputs/_diagnostics/controlled_paired_reanalysis_adr0059.py`.

### Intersection of survivors

Union of aborted tasks across both scenarios: `135a2760`, `4c416de3`,
`9bbf930d`, `d59b0160`, `dfadab01` (5 tasks). The intersection, i.e.
tasks not aborted in **either** scenario, is exactly **7 of the
original 12**: `20270e3b`, `28a6681f`, `3dc255db`, `7b5033c1`,
`8698868d`, `a251c730`, `dbff022c`.

This intersection happens to equal the warm-started scenario's own full
surviving set (it lost no additional tasks beyond the union), while it
drops 2 tasks (`9bbf930d`, `d59b0160`) that baseline had completed but
warm-started had not.

### Reproducing the original figures (methodology check)

Before trusting the recalculation, the exact `per_cell_accuracy_distribution`
logic from `validation_run_summary.py` was reapplied to all persisted
rows to confirm it reproduces the original table exactly. It does:
baseline 0.8291104... (rounds to 0.8291) and warm-started 0.9269362...
(rounds to 0.9269), both exact matches. This also resolves an open
question about the reported `n`: it is `len(split_rows)`, the total
count of test-split rows across surviving tasks (10 for baseline, 8 for
warm-started), **including** rows whose
`constrained_best_cell_accuracy` is `null` (they count toward `n` but
not toward the mean). Baseline has only 5 of its 10 test rows
measurable; warm-started has only 3 of its 8.

### Controlled table, restricted to the 7-task intersection

| Scenario | exact_match_rate_test | per_cell_accuracy (mean, n, n_measurable) | close/middling/far |
|---|---|---|---|
| `baseline_no_pretraining` | 0.0000 | 0.8882 (n=8, measurable=3) | 3/0/5 |
| `warm_started_from_pretraining_v3` | 0.0000 | 0.9269 (n=8, measurable=3) | 3/0/5 |

Warm-started's controlled numbers are identical to its original,
uncontrolled numbers, since its own surviving set already equals the
intersection exactly. Baseline's controlled mean rises slightly from
0.8291 to 0.8882 relative to its original figure, because the 2 tasks
dropped from the intersection (`9bbf930d`, `d59b0160`) happened to have
comparatively lower measurable accuracy in baseline's own original set.

Per-task test accuracies within the intersection (both scenarios saw
the same tasks, letting direct pairing):

| Task | baseline test acc(s) | warm-started test acc(s) |
|---|---|---|
| `20270e3b` | null, null | null, null |
| `28a6681f` | 0.89 | 0.91 |
| `3dc255db` | 0.8397 | 0.9359 |
| `7b5033c1` | null | null |
| `8698868d` | null | null |
| `a251c730` | null | null |
| `dbff022c` | 0.9349 | 0.9349 (unchanged) |

Only 3 of the 7 intersection tasks have any measurable held-out cell
accuracy at all in either scenario; the other 4 total-parse-failed on
their single test pair in both scenarios identically (`parse_failure_delta=0`,
consistent with the original report).

### Controlled gain vs. noise floor and original gain

- **Controlled gain:** 0.9269 - 0.8882 = **+0.0387** (about **6.9x**
  ADR 0039's noise floor of 0.0056, still above the pre-registered 3x
  threshold, so `exceeds_noise_floor_by_multiple` stays `True` under
  the controlled figures).
- **Original (uncontrolled) gain:** +0.0978 (about 17.5x the noise
  floor).
- The controlled, paired gain is **smaller than the original gain**,
  roughly 40% of it (0.0387 vs. 0.0978). Part of the original gain was
  indeed an artifact of comparing warm-started's smaller, easier
  surviving subset against baseline's larger, harder one, as
  suspected. The controlled gain does not vanish and does not flip
  sign - it remains a real, positive, above-noise-floor gain, just a
  materially smaller one than the headline figure suggested.

### exact_match confirmation

`exact_match_rate_test` stays **0.0000** in both scenarios when
restricted to the 7-task intersection, confirmed explicitly (0 of 8
test rows in either scenario have `constrained_exact_match=true`).
Unchanged from the original report, as expected.

### What this does and does not settle

This reanalysis removes the specific comparability confound the
original table did not account for. It does not by itself decide
whether to scale to 400-600 tasks, retry at an intermediate scale, or
treat ADR 0057's abandonment criteria as met - per the user's explicit
instruction, that decision is left to the user, informed by this
controlled number (+0.0387, ~6.9x noise floor) together with ADR
0059's already-reported real time cost (18.91-126.31h for 400-600
tasks) and the still-zero held-out `exact_match` in both scenarios.

## Alternatives considered

- **Treat `should_scale=True` as sufficient on its own and proceed to
  400-600 tasks:** rejected. The pre-registered formula does not
  account for the circuit-breaker abort asymmetry or the
  smaller-surviving-subset comparability confound found in this run;
  applying the formula literally without surfacing those caveats would
  misrepresent the strength of the signal to the user, whose explicit
  request was to weigh generalization signal and time cost together
  before any scaling decision.
- **Re-run the pilot at the same 120/12 scale to isolate the
  comparability confound (e.g. compare only tasks that completed in
  both scenarios) before reporting:** deferred, not rejected outright.
  This is a reasonable follow-up diagnostic, but it does not change the
  measured real penalty ratio or the recalculated time estimate, the
  two pieces of information the user explicitly asked to see before
  deciding whether to scale; running it first would delay that
  decision without changing its two main inputs.
- **Discard the run and treat the abort-asymmetry as disqualifying on
  its own:** rejected. The user's pre-registered criteria (ADR 0057)
  do not include this as an abandonment criterion, and unilaterally
  adding a new one after seeing the result would not respect the
  pre-registration discipline the user explicitly asked for.

## References

- [ADR 0022 - Hypothesis reformulation after the pre-existing-augmentation discovery](0022-hypothesis-reformulation-post-augmentation-discovery.md)
- [ADR 0036 - Cross-task pretraining pilot (real run, partial)](0036-piloto-pretreino-cross-task.md)
- [ADR 0039 - Cross-task pretraining pilot v2, paired comparison](0039-piloto-pretreino-v2-comparacao-pareada.md)
- [ADR 0049 - Time-budgeted hybrid symbolic+neural submission pipeline](0049-pipeline-hibrido-orcamento-tempo.md) (per-task neural time circuit breaker section)
- [ADR 0055 - Qwen3-4B-Base vs Instruct](0055-qwen3-base-vs-instruct.md)
- [ADR 0056 - Parser leniency fix and 4-failure-mode mitigation for Qwen3-4B-Base](0056-mitigacao-4-modos-qwen3-base.md)
- [ADR 0057 - Sizing a larger-scale cross-task pretraining attempt, Qwen3-4B-Base](0057-dimensionamento-pretreino-v3-qwen3-base.md)
- [ADR 0058 - Circuit breaker wiring through the diagnostic path](0058-circuit-breaker-wiring-diagnostic-path.md)
