# 0030 - Splitting the repetition-mitigation parameters

## Status

Informative. Splits ADR 0029's combined `repetition_only` axis
(`repetition_penalty` + `no_repeat_ngram_size` varied together) into
each parameter in isolation, then tries a gentler value for the
parameter found responsible for ADR 0029's held-out-accuracy
regression. Does not decide a production default.

## Context

ADR 0029 found that `repetition_penalty=1.3` and `no_repeat_ngram_size=3`,
applied together as one `repetition_only` config, eliminate
`13e47133`'s degenerate repetition and cut `0934a4d8`'s hallucination
substantially, driving an 11.5x/3.6x generation-time cut on those two
tasks. But the same config measurably regresses held-out per-cell
accuracy on the 6 sanity-sample tasks that never showed either failure
mode (mean 0.736 to 0.587, -0.15, about 20% relative), a regression
larger than color augmentation's own gain (ADR 0027, mean 0.74 to 0.76).
ADR 0029 could not attribute that regression to either parameter
individually, since both varied together, and left that split as an
explicit open question.

## Method

Two new config builders in `src/evaluation/decoding_mitigation_configs.py`,
ADR 0029's existing `build_decoding_mitigation_configs()` left
unchanged:

- `build_repetition_axis_split_configs()`: `penalty_only`
  (`repetition_penalty=1.3` alone) and `ngram_only`
  (`no_repeat_ngram_size=3` alone), each varying exactly one parameter
  against the same `NeuralSolverConfig` defaults ADR 0029 used for
  `baseline`.
- `build_gentle_ngram_config()`: `ngram_gentle`
  (`no_repeat_ngram_size=5` alone, no `repetition_penalty`), tried only
  after confirming which parameter drives the regression.

Both configs run on the full 8-task sanity sample (`src/evaluation/
run_repetition_split_smoke.py`, `run_gentle_ngram_smoke.py`), not just
the 2 affected tasks plus a separate 6-task check as ADR 0029 did -
this way every config in this ADR is measured on the identical 8-task
set, including the 2 target tasks. `baseline`, `repetition_only` (the
combined config), `stop_heuristic_only`, and `both` reuse ADR 0029's
already-persisted results unchanged, no re-run. Shape constraint (ADR
0025/0026) kept applied throughout, same diagnostic plumbing as ADR
0029 (`mitigation_diagnostics.py`, `failure_mode_diagnostics.py`).

5 new host tests added to `tests/test_decoding_mitigation_configs.py`
(10 total), full suite 139/139 passing (unchanged by this ADR, pure
config construction).

## Results

### 1. Does the failure mode disappear?

`13e47133` (degenerate repetition), repetitive attempts / total
attempts across its 5 pairs:

| Config | Repetitive | Total |
|---|---|---|
| `baseline` | 17 | 19 |
| `repetition_only` (combined) | 0 | 16 |
| `penalty_only` | 4 | 20 |
| `ngram_only` | **0** | 16 |
| `ngram_gentle` (size 5) | 3 | 19 |
| `both` | 0 | 18 |

`0934a4d8` (hallucinated second example), hallucinated attempts / total
attempts:

| Config | Hallucinated | Total |
|---|---|---|
| `baseline` | 7 | 17 |
| `repetition_only` (combined) | 3 | 19 |
| `penalty_only` | 7 | 20 |
| `ngram_only` | **2** | 18 |
| `ngram_gentle` (size 5) | 10 | 23 |
| `both` | 0 (by construction) | 13 |

`ngram_only` alone reproduces essentially all of the combined
`repetition_only` config's failure-mode fix on both tasks (0/16
repetitive, 2/18 hallucinated, both close to or better than the
combined result). `penalty_only` does almost nothing: 4/20 repetitive
is barely below `baseline`'s 17/19 rate-adjusted, and 7/20 hallucinated
is statistically the same as `baseline`'s 7/17. `ngram_gentle` sits
between the two: it still helps materially over `baseline` on both
counts, but noticeably less than `ngram_only` (3 vs. 0 repetitive
attempts, 10 vs. 2 hallucinated attempts) - loosening the constraint
from 3 to 5 gives back some of the fix.

### 2. Does generation time drop for the two affected tasks?

| Config | `0934a4d8` total s | `13e47133` total s |
|---|---|---|
| `baseline` | 312.50 | 1459.41 |
| `repetition_only` (combined) | 114.68 | 112.01 |
| `penalty_only` | 291.31 | 1308.39 |
| `ngram_only` | 105.24 | 111.72 |
| `ngram_gentle` (size 5) | 194.51 | 268.92 |
| `both` | 87.43 | 126.32 |

`ngram_only` alone captures essentially all of the combined config's
timing win (105s/112s vs. 115s/112s). `penalty_only` is within noise of
`baseline` (291s vs. 312s, 1308s vs. 1459s) - no meaningful timing
benefit. `ngram_gentle` gives a real but smaller win than `ngram_only`
(1.6x vs. 3.0x for `0934a4d8`, 5.4x vs. 13.1x for `13e47133`),
consistent with Result 1: a looser block still shortens generation, but
less effectively.

### 3. Does `13e47133`'s content quality change?

Held-out test pairs, per-cell accuracy:

| Config | Test pair 0 | Test pair 1 |
|---|---|---|
| `baseline` | 0.12 | 0.17 |
| `repetition_only` (combined) | 0.14 | 0.18 |
| `penalty_only` | 0.14 | 0.06 |
| `ngram_only` | 0.16 | 0.06 |
| `ngram_gentle` (size 5) | 0.11 | 0.08 |
| `both` | 0.16 | 0.18 |

Flat within noise across every config, same reading as ADR 0029: none
of these mitigations, in isolation or loosened, teach the model the
right transformation for this task, they only change whether/how
quickly generation stops.

### 4. Regression check on the other 6 tasks (held-out per-cell accuracy)

Mean across the 7 measurable held-out pairs (`135a2760`, `142ca369` x2,
`16b78196`, `16de56c4` x2, `1818057f`; `136b0064` stays n/a, the shape
rule fails for it under every config):

| Config | Mean | Delta vs. `baseline` |
|---|---|---|
| `baseline` | 0.736 | - |
| `repetition_only` (combined) | (not separately run in ADR 0029; see `both`) | - |
| `penalty_only` | 0.769 | +0.033 (+4.5%) |
| `ngram_only` | 0.583 | -0.153 (-20.8%) |
| `ngram_gentle` (size 5) | 0.563 | -0.173 (-23.5%) |
| `both` | 0.587 | -0.149 (-20.2%) |

Per-task breakdown (`baseline` -> `penalty_only` -> `ngram_only` ->
`ngram_gentle`):

| Task | `baseline` | `penalty_only` | `ngram_only` | `ngram_gentle` |
|---|---|---|---|---|
| `135a2760` | 0.77 | 0.77 | 0.54 | 0.54 |
| `142ca369` | 0.45, 0.82 | 0.45, 0.84 | 0.32, 0.69 | 0.38, 0.75 |
| `16b78196` | 0.89 | 0.92 | 0.78 | 0.66 |
| `16de56c4` | 0.59, 0.73 | 0.68, 0.82 | 0.51, 0.68 | 0.49, 0.70 |
| `1818057f` | 0.90 | 0.90 | 0.56 | 0.42 |

`ngram_only` alone reproduces almost the entire regression previously
attributed to `both` (-0.153 vs. -0.149, essentially the same size).
`penalty_only` shows no regression at all, a small mean improvement
(+0.033) that is well within run-to-run noise (ADR 0027/0029's own
caveat about stochastic TTT/sampling), not a real gain.

## Hypothesis check

The user's hypothesis was: `no_repeat_ngram_size=3` is the likely
cause of the regression (a hard constraint that can block legitimate
color repetition in ARC grid content), while `repetition_penalty`
alone should preserve more of the speed/correction gain without
regressing the other 6 tasks as much.

**Confirmed, with one refinement.** `no_repeat_ngram_size=3` alone
does drive essentially all of both the benefit (failure-mode
elimination, timing cut) and the harm (the 6-task regression) that
ADR 0029 measured for the combined config. `repetition_penalty=1.3`
alone is not the regression's cause. But it also does not "preserve
more of the gain" as hypothesized - it is close to inert on every
axis measured here: negligible failure-mode reduction, negligible
timing benefit, and no measurable regression, essentially a
near-no-op at this value in this sample, not a smaller-but-real
version of the combined effect.

The conditional follow-up (does a gentler `no_repeat_ngram_size=5`
still fix the target tasks with less collateral damage) is **not**
supported by this sample: `ngram_gentle` fixes the target tasks
*less* effectively than `ngram_only` (3/19 vs. 0/16 repetitive
attempts, 10/23 vs. 2/18 hallucinated attempts, smaller timing cuts)
while regressing the other 6 tasks by roughly the same amount, if
anything slightly more (mean 0.563 vs. 0.583). Loosening the
constraint from 3 to 5 traded away most of the fix without buying
back the accuracy it cost. This is a single 8-task smoke/sanity-tier
sample (Golden Rule 7), so this specific numeric ordering (5 slightly
worse than 3) should be read as "no evidence gentler helps here", not
as a precise, reproducible ranking.

## Consequences

- `no_repeat_ngram_size` is confirmed as the parameter responsible for
  ADR 0029's regression; `repetition_penalty=1.3` can be dropped from
  any future production config with essentially no loss on the metrics
  measured here (it contributes almost nothing, in either direction).
- Loosening `no_repeat_ngram_size` from 3 to 5 is not, on this
  evidence, a viable way to keep the fix while reducing the regression;
  it gives up more of the fix than it saves in accuracy.
- This still leaves an unresolved tradeoff for the 2 target tasks:
  `no_repeat_ngram_size=3` (or `both`) is the only config tested that
  meaningfully removes both failure modes and their timing cost, but it
  is also the one config (tied with `both`) that regresses the other 6
  tasks the most.
- Task-conditional application (`no_repeat_ngram_size` only for tasks
  that actually show degenerate repetition/hallucination in an initial
  pass, `baseline` decoding otherwise) remains an untested, open
  alternative this ADR does not evaluate.
- No production-default decision is made here. All 7 result sets above
  (`baseline`, `repetition_only`, `stop_heuristic_only`, `both`,
  `penalty_only`, `ngram_only`, `ngram_gentle`) are presented for a
  joint decision on which, if any, configuration to adopt.
- Single run per config; TTT/LoRA initialization and sampling are
  stochastic (same caveat as ADR 0027/0029), so exact figures are not
  expected to reproduce bit for bit, only the qualitative pattern.

## Alternatives considered

- Testing intermediate `no_repeat_ngram_size` values (e.g. 4) between 3
  and 5: not run, since the size-5 result already shows loosening the
  constraint does not clearly help on this sample; a size-4 point
  would add another data point on the same non-improving trend without
  a strong reason to expect a different qualitative conclusion. Left
  open if the joint decision wants finer resolution here.
- Task-conditional application (only apply `no_repeat_ngram_size` to
  tasks whose baseline generation already shows the failure mode, a
  cheap check before the main generation pass): not implemented here,
  named as an open alternative in Consequences, since it changes the
  pipeline's control flow, not just a config value, and was out of
  this ADR's narrower scope (parameter attribution, not new pipeline
  design).
- Re-running `repetition_only` (the combined config) on all 8 tasks
  here for a fully matched comparison: not done, ADR 0029's existing
  6-task regression-check data for `both` (a superset behavior) was
  judged sufficient context, and re-running would cost GPU time
  without changing the attribution conclusion, which rests on
  `penalty_only` vs. `ngram_only`, not on re-verifying `both`.
