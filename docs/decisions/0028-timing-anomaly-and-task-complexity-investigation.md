# 0028 - Timing anomaly and task complexity investigation

## Status

Informative. Does not implement any fix. Determines whether the
`0934a4d8`/`13e47133` generation-timing anomaly (flagged unresolved in
ADR 0023, ADR 0026, ADR 0027) is an expected property of larger/more
complex tasks, or a specific, fixable generation behavior. Answers the
four questions posed for this investigation using only data already
persisted by those three ADRs' runs; no new GPU run was performed.

## Context

ADR 0023 first observed that `0934a4d8` and `13e47133` take far more
total wall time than their own TTT time would predict. ADR 0026 and
ADR 0027 both re-observed the same two tasks showing the same pattern,
across three different configs (no shape constraint, shape constraint,
shape constraint plus color augmentation), without investigation. ADR
0026 also independently flagged `13e47133` as "far" in content quality
(lowest `constrained_best_cell_accuracy`, the only task with a parse
failure). This ADR investigates whether these two facts share a cause.

## Method

Reused, no new run:

- `src/utils/task_loader.py` and `src/evaluation/sample_tiers.py` to
  recover the exact 8-task sanity sample and each task's raw grid
  dimensions from `data/ARC-AGI-2/data/evaluation`.
- Persisted diagnostic rows (`attempts_tried`, `num_parsed`, `num_kept`,
  `rule_holds`) from three independent runs: `outputs/diagnostics/sanity_current_config/`
  (ADR 0023), `outputs/diagnostics/shape_constraint_sanity/` (ADR 0026),
  `outputs/diagnostics/color_augmentation_sanity/` (ADR 0027, both
  `geometric_only` and `geometric_plus_color`).
- Persisted raw completions in the matching `outputs/raw_generations/`
  subdirectories: file size as a token-length proxy, and file
  modification timestamps (each pair's attempts are written together as
  a batch right after that pair's generation loop finishes) to
  reconstruct per-pair wall-clock gaps.
- `src/solvers/neural/generation.py` and `src/evaluation/generation_diagnostics.py`
  to confirm the retry mechanism: `num_predictions=2`,
  `_MAX_SAMPLING_ATTEMPTS_PER_PREDICTION=3`, so `max_attempts=6` per
  pair; the loop calls `model.generate()` once per attempt and keeps
  going, up to that cap, until enough completions parse into distinct
  valid grids.

## Results

### 1. Structural comparison

| Task | Train pairs | Test pairs | Max input cells | Max output cells | Max out/in ratio | Shape rule holds (ADR 0025) |
|---|---|---|---|---|---|---|
| `0934a4d8` | 4 | 1 | 900 | 36 | **0.04** | No |
| `13e47133` | 3 | 2 | 900 | 900 | 1.00 | Yes |
| `135a2760` | 2 | 1 | 841 | 841 | 1.00 | Yes |
| `136b0064` | 3 | 1 | 285 | 133 | 0.47 | No |
| `142ca369` | 3 | 2 | 400 | 400 | 1.00 | Yes |
| `16b78196` | 2 | 1 | 900 | 900 | 1.00 | Yes |
| `16de56c4` | 3 | 2 | 189 | 189 | 1.00 | Yes |
| `1818057f` | 3 | 1 | 484 | 484 | 1.00 | Yes |

`0934a4d8` is a genuine outlier: it is an extraction-style task (large
30x30 inputs, tiny outputs of 16-36 cells), with by far the most
extreme output/input size ratio in the sample (0.04, next closest is
`136b0064` at 0.47). It is one of only two tasks (with `136b0064`)
where ADR 0025's "output shape equals input shape" rule does not hold.

`13e47133` is **not** structurally distinguished from the other tasks:
it shares its 900-cell same-shape grids with `16b78196` (no anomaly),
its 3-train-pair count with three other tasks, and its 2-test-pair
count with `142ca369`/`16de56c4` (neither anomalous). Its shape rule
holds, same as five of the other six tasks. Grid size and pair count
alone do not explain its anomaly; something else does (see Results 2-4).

`136b0064` also fails the shape rule but shows no timing anomaly in any
run, which rules out "shape rule fails" as a sufficient explanation on
its own.

### 2. Where the extra time goes

Not TTT, not pre/post-processing. ADR 0027 already logged TTT time for
these two tasks as unremarkable (80s and 43s under `geometric_only`,
against 1167s and 1112s total), and the shape constraint is a cheap
deterministic truncate/pad (ADR 0025). The persisted `attempts_tried`
counts confirm the extra time is in the generation/self-consistency
retry loop:

| Run | `0934a4d8` total attempts | `13e47133` total attempts | Next-highest task in the same run |
|---|---|---|---|
| ADR 0023 (`sanity_current_config`) | 24 | 19 | 12 (`16de56c4`) |
| ADR 0026 (`shape_constraint_sanity`) | 22 | n/a (not re-tabulated, same pattern) | ~8-11 for the rest |
| ADR 0027 `geometric_only` | 28 | 17 | 14 (`1818057f`) |
| ADR 0027 `geometric_plus_color` | 10 | 12 | 14 (`142ca369`/`16de56c4`) |

Under `geometric_only`, both tasks repeatedly hit the hard cap of 6
attempts per pair (e.g. `0934a4d8` train pairs 1-3 all show
`attempts_tried=6`; `13e47133` train pair 2 shows `attempts_tried=6,
num_kept=0`, a complete parse failure after exhausting every attempt).

Raw completion sizes (a token-length proxy) show why: the failed
attempts are individually much longer than a valid completion, not
merely more numerous.

- `0934a4d8` train pair 1 (expected output: 20 cells): five of six
  attempts are 26-501 bytes, but one is 2767 bytes, an outlier nearly
  6x the next-largest sibling. Reading it shows the model completed the
  correct small grid, then kept generating an `Output:` / `Input:`
  block and a full hallucinated second example, instead of stopping.
- `13e47133` train pair 2 (expected output: 130 cells): all six
  attempts are within 2380-2395 bytes, uniformly near the
  `max_new_tokens=1024` cap. Reading one shows degenerate repetition:
  dozens of consecutive identical rows (e.g. `6666666666666` repeated
  over 100 times), never reaching a valid, terminated grid.

File modification timestamps on the persisted `outputs/raw_generations/sanity_current_config/`
directory (each pair's attempts are batch-written once that pair's
retry loop finishes) reconstruct the per-pair wall-clock cost directly:
`0934a4d8` train pair 2 (6 attempts, one long outlier) took ~155s vs.
train pair 1 (6 attempts, no long outlier) at ~58s; `13e47133` train
pair 2 (6 attempts, all near-max-length) took ~602s, the single
largest per-pair gap observed anywhere in the sample.

### 3. Relationship to grid size

Disproportionate, not proportional. `16b78196` has the identical
maximum grid size (900 cells, 30x30) as both anomaly tasks, yet shows
uniformly minimal attempts (6-8 total, 2-3 per pair) in every run, no
anomaly at all. Conversely, smaller tasks (`16de56c4` at 189 cells,
`1818057f` at 484 cells) occasionally show an isolated 6-attempt spike
on one pair, unrelated to being consistently large. Grid size does not
predict the anomaly; the generation pathology described in Result 2
does, and it concentrates on `0934a4d8`/`13e47133` far more
consistently (multiple pairs, every run) than on any other task (at
most one pair, one run).

### 4. Relationship to `13e47133`'s "far" content classification

For `13e47133`, yes, both symptoms share one root cause. The same raw
completions that fail to parse (degenerate token repetition, never
reaching a valid terminated grid) are also the ones that run to the
token cap and drive the timing anomaly. The model has not learned this
task's transformation confidently enough to produce a short, correct,
self-terminating completion, so sampling collapses into repetition,
which shows up simultaneously as low content accuracy (ADR 0026/0027)
and as slow generation (this ADR). This is consistent with, and adds a
mechanism to, ADR 0026's reading of `13e47133` as a distinct failure
mode from the five "close" tasks.

For `0934a4d8`, the link is only suggestive, not measurable: it was
never part of ADR 0026/0027's close/far classification to begin with,
because its shape rule does not hold, so `constrained_best_cell_accuracy`
is `None` for every one of its rows. Its dominant failure mode is also
different in kind, hallucinating a second, plausible-looking
`Input:`/`Output:` example rather than degenerating into repetition,
which looks more specifically tied to its extreme output/input size
mismatch (Result 1) than to a general content/generalization gap.

## Consequences

- The anomaly is not an expected, size-proportional cost of larger
  grids; it is a generation-side pathology (non-terminating
  completions consuming the full retry budget) concentrated on two
  specific tasks, worth fixing rather than budgeting around.
- For `13e47133` specifically, the same evidence that explains the
  timing anomaly also explains part of its content gap: the model's
  low-confidence output on this task manifests as degenerate
  repetition, which is both wrong and slow. Any future generalization
  fix that raises the model's confidence on `13e47133`'s transformation
  is likely to reduce its timing anomaly as a side effect (partially
  observed already: `geometric_plus_color` in ADR 0027 both improved
  `13e47133`'s training-pair parsing and roughly halved its total
  time relative to `geometric_only`, 567s vs. 1112s).
- For `0934a4d8`, the mechanism is the same retry-loop-hits-cap
  pattern, but the trigger looks distinct (extreme output/input size
  ratio inviting a hallucinated continuation, not repetition), so a
  `13e47133`-targeted content fix is not guaranteed to resolve
  `0934a4d8`'s anomaly the same way.
- No fix is implemented here per the explicit scope of this ADR. A
  plausible, not yet decided, future lever: constrain or terminate
  generation once the expected output size (when knowable, e.g. under
  the ADR 0025 shape rule, or a max-cells heuristic otherwise) is
  reached, instead of relying solely on the model's own EOS timing;
  this would need its own ADR before implementation.
- Confirms the anomaly is orthogonal to the shape constraint (ADR 0025)
  and to color augmentation (ADR 0027) as fixes: both changed its
  magnitude somewhat but neither changed its presence, since it also
  appears in ADR 0023's pre-shape-constraint, pre-color-augmentation
  baseline run.
- Answers the open item ADR 0027 flagged as worth prioritizing before
  it confounds a `validation`-layer timing budget (ADR 0013): the risk
  is real, since nothing rules out other tasks in a 30-50 task sample
  exhibiting the same non-terminating-completion pathology.

## Alternatives considered

- Running a fresh diagnostic GPU pass instrumented with explicit
  per-`model.generate()` timers: rejected for this ADR, since the
  persisted `attempts_tried` counts, raw completion sizes, and file
  timestamps from three already-completed runs were sufficient to
  answer all four questions without new GPU time, per the explicit
  instruction to reuse existing data first. A future fix's validation
  may still want direct per-call timers.
- Treating the anomaly as purely a `13e47133`-content problem and
  closing `0934a4d8` as unrelated: rejected, both tasks share the same
  underlying mechanism (retry loop exhausted by non-terminating
  completions), even though the trigger differs; documenting both under
  one investigation keeps that shared mechanism visible for whoever
  designs the fix.
