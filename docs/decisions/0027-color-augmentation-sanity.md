# 0027 - Color augmentation at the sanity layer

## Status

Informative. Does not decide whether color augmentation becomes a
production default, and does not change the tested permutation count
(2 color variants per pair, on top of the existing 8-transform D4
geometric augmentation). Presents sanity-tier evidence for a joint
decision, per the standing lean recorded in ADR 0026.

## Context

ADR 0026 (sanity-tier, 8 tasks/11 test pairs, same sample as
ADR 0017/0023/0024) found a wide per-cell-accuracy spread once shape
stopped confounding the read (0.19-0.90), with 5/8 rule-holding pairs
"close" and `13e47133` clearly "far" across three converging signals.
It recorded an initial, non-final lean toward trying color augmentation
first, as the smaller/cheaper of the two ADR 0022 content-lever
candidates.

This run implements color augmentation (`src/solvers/neural/color_augmentation.py`):
color 0 (background) stays fixed, only the non-zero colors present in a
task are permuted, 2 permutations per train pair (`num_color_augmentations_per_pair`
default), applied only to train/demonstration pairs, never to the test
input. It is gated by `use_color_augmentation` on `NeuralSolverConfig`
(default off) and composes with the existing geometric augmentation
(ADR 0021) rather than replacing it.

## Method

`src/evaluation/run_color_augmentation_sanity.py`, same 8-task sample as
ADR 0017/0023/0024/0026 (`select_tier_tasks(tasks, "sanity")`), same
shape constraint applied (ADR 0025/0026) so results stay readable
without shape as a confound. Two configs
(`src/evaluation/color_augmentation_configs.py`):

- `geometric_only`: `use_geometric_augmentation=True`, `use_color_augmentation=False` (the ADR 0026 baseline, re-run fresh, not reused, since TTT involves randomness).
- `geometric_plus_color`: same, plus `use_color_augmentation=True`, `num_color_augmentations_per_pair=2`.

Both configs run end to end (fresh LoRA, TTT, generation, shape
constraint) for all 8 tasks, 16 `Trainer.train()` runs total. `Num
examples` in the training logs confirms the multiplier is applied as
designed (e.g. a 2-train-pair task: 48 examples = 2 pairs x 8 geometric
transforms x 3 color variants including the identity mapping).

## Results

### 1. Per-cell accuracy on the 5 "close" tasks (`135a2760`, `142ca369`, `16b78196`, `16de56c4`, `1818057f`)

Held-out test pairs, `geometric_only` -> `geometric_plus_color`:

| Task | Test pair | geometric_only | geometric_plus_color | Change |
|---|---|---|---|---|
| `135a2760` | 0 | 0.77 | 0.77 | 0 |
| `142ca369` | 0 | 0.45 | 0.48 | +0.03 |
| `142ca369` | 1 | 0.84 | 0.84 | 0 |
| `16b78196` | 0 | 0.89 | 0.92 | +0.03 |
| `16de56c4` | 0 | 0.59 | 0.67 | +0.08 |
| `16de56c4` | 1 | 0.73 | 0.80 | +0.07 |
| `1818057f` | 0 | 0.89 | 0.81 | -0.08 |

Mean across these 7 held-out pairs: 0.74 -> 0.76 (+0.02). 4 pairs
improve, 2 are unchanged, 1 regresses (`1818057f`). Not a uniform win,
but net positive and no case gets meaningfully worse except that one.

Training pairs (in-distribution) show a stronger, more consistent
improvement, most visibly for `16de56c4` (all three train pairs reach
`exact_match`) and `1818057f` (one train pair reaches `exact_match`).
Full per-pair training-pair accuracy is in the raw run log
(`outputs/diagnostics/color_augmentation_sanity/`); the shape of the
result, larger gains on train than on held-out test, is the same
textbook overfitting signature ADR 0019 flagged for the epochs/LoRA
axis, this time for the augmentation axis.

### 2. Does any `exact_match` appear?

Yes, 5 rows, all under `geometric_plus_color`, all on training pairs,
none on held-out test pairs:

| Task | Split | Pair |
|---|---|---|
| `135a2760` | train | 0 |
| `16de56c4` | train | 0 |
| `16de56c4` | train | 1 |
| `16de56c4` | train | 2 |
| `1818057f` | train | 1 |

0/11 held-out test pairs reach `exact_match` in either config. This is
the first time any row in this diagnostic chain (ADR 0017 through 0026)
has reached `exact_match` at all, but the fact that it is exclusively on
pairs the model trained on directly means it cannot yet be read as a
generalization win, only as evidence the model can fit augmented data
tightly enough to reproduce it exactly.

### 3. Does `13e47133` change?

Held-out test cell accuracy stays in the same "far" range: 0.23/0.12
(`geometric_only`) vs. 0.20/0.18 (`geometric_plus_color`), one pair down
slightly, one up slightly, no material change and still well below the
5 close tasks. These values also differ somewhat from ADR 0026's
0.19 for this task; both runs sample a fresh TTT/LoRA initialization
and generation, so exact figures are not expected to reproduce bit for
bit, only to stay in the same qualitative range, which they do.

Two things did change on `13e47133`, both on the training side:

- Training-pair cell accuracy rose across the board: 0.37 -> 0.57,
  0.39 -> 0.62, and a third train pair that failed to parse anything
  under `geometric_only` (`n/a`) parsed successfully under
  `geometric_plus_color` (0.66).
- The parse failure that appeared in this run's `geometric_only`
  baseline did not recur anywhere under `geometric_plus_color` for this
  task (all 5 of its pairs parsed).

So color augmentation measurably helped `13e47133` fit and parse its
own training pairs, without moving its held-out test accuracy out of
the "far" range. This is consistent with ADR 0026's reading of
`13e47133` as a different failure mode from the 5 close tasks (a
capability gap, not a near-miss), since the training-pair improvement
did not transfer to the test pairs the way it did for the close tasks.

### 4. Time cost of color augmentation vs. geometric-only

| Config | Mean TTT seconds/task | Mean total seconds/task (all 8) | Mean total seconds/task (6, excludes 2 timing-anomaly tasks) |
|---|---|---|---|
| `geometric_only` | 41.9 | 418.6 | 178.4 |
| `geometric_plus_color` | 117.5 | 270.5 | 232.8 |

TTT itself is about 2.8x slower under `geometric_plus_color`
(consistent with the roughly 3x per-pair example multiplier from adding
2 color variants). Total wall time per task (TTT + generation +
self-consistency) is a smaller multiplier, about 1.3x, on the 6 tasks
that ran at a normal pace, because generation, not TTT, dominates total
time for this config.

Two tasks (`0934a4d8`, `13e47133`) show the same unexplained
generation-timing anomaly ADR 0023/0026 already flagged (total time far
exceeding TTT time: `geometric_only` shows 1167s and 1112s total for
tasks whose TTT itself only took 80s and 43s). The anomaly recurs under
`geometric_only` in this run and is smaller but still present under
`geometric_plus_color` (200s and 567s total for the same two tasks).
Still not investigated; excluded from the "6 tasks" column above so it
does not distort the color-augmentation timing comparison, but it
remains an open item independent of this ADR.

## Consequences

- First appearance of `exact_match` anywhere in this diagnostic chain,
  though confined to training pairs; on its own this does not establish
  that color augmentation improves held-out generalization.
- Net positive but non-uniform effect on held-out per-cell accuracy for
  the 5 "close" tasks (4 up, 2 unchanged, 1 down), at roughly 2.8x TTT
  time and roughly 1.3x total wall time per task (excluding the known
  timing anomaly).
- `13e47133` stays in the "far" category on held-out data even with
  color augmentation, despite measurable gains on its own training
  pairs, reinforcing ADR 0026's reading that it is a different failure
  mode from the 5 close tasks rather than a smaller version of the same
  gap.
- Per Golden Rule 7, this sanity-tier result (n=8) cannot by itself
  justify adopting color augmentation as a production default, changing
  the permutation count, or retiring the geometric-only baseline. A
  `validation`-layer run (30-50 tasks) is the bar for any of those
  decisions.
- The generation-timing anomaly on `0934a4d8`/`13e47133` recurs across
  three ADRs now (0023, 0026, this one) without investigation; worth
  prioritizing before it confounds a future validation-layer timing
  budget read (ADR 0013).

## Alternatives considered

- Reusing ADR 0026's already-persisted `geometric_only` rows instead of
  re-running that config: rejected, TTT/LoRA initialization and
  sampling are stochastic, so a fresh same-config run is needed for a
  fair paired comparison against `geometric_plus_color` run in the same
  session, rather than comparing against a run from a different day
  under different random draws.
- Testing more than 2 color permutations per pair in this same run, to
  see if a larger count moves the needle further: rejected per the
  explicit scope of this ADR, changing the permutation count is a
  separate decision the results here should inform, not preempt.
- Dropping the shape constraint for this run to isolate color
  augmentation's effect from ADR 0025/0026's shape fix: rejected, the
  point is to measure color augmentation's effect on top of the current
  best-known config, not in isolation from it; an unconstrained-vs-color
  comparison would reintroduce the shape confound ADR 0025/0026 already
  closed.
