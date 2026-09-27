# 0037 - Error pattern diagnosis on "close" held-out pairs

## Status

Informative.

## Context

ADR 0034's real validation run (40 tasks, 54 held-out test pairs) found
`exact_match_rate_test=0.0000` but a bimodal `constrained_best_cell_accuracy`
distribution: close=23, middling=9, far=22 (thresholds from
`validation_run_summary.py`: close >= 0.7, far < 0.3). The 23 "close" pairs
are the cheapest lever candidate available today: no new GPU run, reusing
only what ADR 0034 already persisted.

Per explicit user request, this ADR investigates, using only persisted data
(no GPU run):

1. Absolute wrong-cell count per close pair (concentrated vs. scattered).
2. Positional pattern of wrong cells (edges/corners/region vs. scattered).
3. Color-substitution pattern (systematic single swap vs. random).
4. Shift/offset pattern (content right, position off, e.g. off-by-one).
5. Close vs. far: shared distinguishing characteristic, or arbitrary.

**Method** (reusing ADR 0028's no-new-GPU-run precedent): the persisted
summary JSONs (`outputs/diagnostics/validation_consolidated_config/evaluation/`)
only carry aggregate accuracy, not grids. The actual predicted grids were
reconstructed by re-parsing the persisted raw completion text files
(`outputs/raw_generations/validation_consolidated_config/evaluation/`)
through the exact same pipeline the original run used
(`grid_serialization.text_to_grid`, then `shape_constraint.force_grid_shape`
gated on `shape_rule.output_shape_equals_input_shape`, matching
`per_attempt_conditional_mitigation_pair_diagnostics._diagnose_pair`), and
diffed cell-by-cell against the expected grid loaded from the task's own
json file. No model/GPU involved; this is pure post-processing over
already-generated text.

## Decision

No fix is implemented in this ADR. Findings only, to inform a joint
decision on the next concrete action.

### Q1: absolute wrong-cell count

Across the 23 close pairs: min 8, max 144, mean 54.0 wrong cells (grid
sizes range 100-900 cells). This is **not** a handful of stray cells: on
average about a third of a pair's wrong-cell budget implied by its
accuracy band is tens of cells, sometimes 100+. Errors are not
concentrated into a small contiguous patch (see Q2); the "close" label
describes a real accuracy band, not near-misses in the naive sense.

### Q2: positional pattern

No consistent geometric bias toward edges/corners/a specific region.
Per-position error rates (wrong-count normalized by how many cells of
each type the grid has) vary widely and inconsistently across pairs:
several pairs have 0% error rate on edges/corners and all error mass in
the interior (`135a2760`, `35ab12c3`, `446ef5d2`, `9aaea919`, `c4d067a0`,
`dbff022c`), but this tracks the interior simply being the largest region
by cell count on those grids, not a targeted region. Other pairs show
non-trivial corner/edge rates (`8f3a5a89`: corner 50%, edge 40%;
`2b83f449`: corner 50%). No pattern generalizes across the sample.
**Conclusion: no exploitable positional pattern.**

### Q3: color-substitution pattern

This is the one signal with real structure, but it is **per-task, not
global**. For each close pair, the single most frequent
(expected-color -> predicted-color) substitution accounts for a
substantial, often dominant, share of that pair's wrong cells:

| Share of wrong cells from the single dominant color swap | Count of pairs (n=23) |
|---|---|
| >= 0.50 | 9 |
| 0.30 - 0.49 | 5 |
| < 0.30 | 9 |
| Mean share | 0.36 |

Examples: `71e489b6` (both test pairs, share 0.65/0.49, swap 7->1 both
times), `b6f77b65` (both test pairs, share 0.20/0.31, swap 3->0 both
times), `c4d067a0` (share 0.56, swap 1->3), `135a2760` (share 0.56, swap
3->8). Where a task has 2 close test pairs, the dominant swap direction
repeats identically in 2 of 3 such tasks (`71e489b6`, `b6f77b65`); the
third (`62593bfd`) shows a different dominant swap per pair (3->1 vs.
1->9).

The specific color pair is **not** shared across different tasks (each
task uses its own swap: 3->8, 7->0, 9->8, 7->1, 9->4, 1->3, ...), which
is expected since ARC color semantics are task-specific, not a universal
palette. So there is no single global "color X is always color Y" bug to
patch with one lookup table. The pattern is: **within a task, the model
tends to consistently confuse one particular pair of colors**, which is
plausibly learnable/correctable per-task from that task's own train
pairs (e.g. detect the dominant train-pair color confusion, if any, and
bias-correct test predictions accordingly), but that is a per-task
adaptive mechanism, not a one-line global fix.

### Q4: shift/offset pattern

Tested every close pair for whether shifting the predicted grid by
`(dr, dc)`, `dr, dc` in `[-2, 2]`, improves the overlap match against the
expected grid relative to the unshifted (0,0) accuracy. Result: **22 of
23 pairs show no improvement from any shift** (the best shift found is
always worse than the actual, unshifted accuracy). The one exception,
`62593bfd` test pair 0, improves marginally (0.955 vs. 0.915 at shift
(-2, 0)), but its sibling test pair 1 of the *same* task does not
(0.958 shift vs. 0.942 baseline, shift does not beat baseline there
either after correction, close call). This is a single, weak,
non-repeating data point, not a pattern. **Conclusion: no off-by-one or
other fixed-shift bug found.** The wrongness is genuine content
disagreement, not a positional bug.

### Q5: close vs. far, distinguishing characteristic

This produced the clearest, most decisive signal of the whole diagnosis.

| | close (n=23) | far (n=22) |
|---|---|---|
| `output_shape_equals_input_shape(task)` true | 23/23 (100%) | 4/22 (18%) |
| Expected grid size (total cells): mean | 387.3 | 387.5 |
| Expected grid size: range | 100-900 | 25-900 |

Grid size is **not** a distinguishing factor at all (nearly identical
means and overlapping ranges). The one variable that separates close
from far almost perfectly is whether the task satisfies the
already-known "output shape equals input shape" rule (ADR 0024/0025):
every one of the 23 close pairs belongs to a task where that rule holds
(and therefore the deterministic shape constraint was applied); 18 of
the 22 far pairs belong to tasks where the rule does not hold (crop,
tile, extract, rescale-shaped transformations), so no shape correction
applies and the raw generation's dimensions are essentially never
right, making `per_cell_accuracy` unmeasurable (`None`, banded as
"far" by convention).

The remaining 4 far pairs (`142ca369`, `36a08778`, `446ef5d2` test pair
0, `c7f57c3e`) do have `rule_holds=True` but still land in "far" for a
separate, already-known reason: total generation parse failure (0 valid
grids parsed across every attempt), unrelated to the shape rule. Notably
`446ef5d2` has one close pair (its other test pair) and one far pair,
confirming that `rule_holds` is a necessary but not sufficient condition,
and that closeness is a pair-level, not purely task-level, outcome.

One further, isolated observation: task `38007db0`'s two far pairs both
produce predictions with **exactly transposed dimensions** relative to
expected (`29x8` expected vs. `8x29`/`15x29` predicted; `25x7` expected
vs. `7x25` predicted). This looks like a real, specific failure mode
(row/column confusion) but is observed in a single task in this sample,
not generalized evidence.

**Conclusion: close vs. far is not arbitrary.** It is overwhelmingly
explained by the pre-existing, already-implemented shape rule from ADR
0024/0025, which currently recognizes exactly one case ("output shape
equals input shape") and leaves every other output-shape-derivation rule
(cropping, tiling, extraction, rescaling, etc.) with no correction at
all.

## Consequences

- No fix implemented. The color-substitution finding (Q3) is real but
  requires a per-task adaptive mechanism (infer the dominant train-pair
  color confusion, correct test predictions), not a universal
  post-processing rule; that is a candidate for a future, separate,
  small ADR + smoke test, not decided here.
- The Q4 shift/offset hypothesis is closed: no evidence supports it.
- The Q2 positional hypothesis is closed as a general rule: no
  consistent bias found in this sample.
- The Q5 finding reframes the "far" bucket: it is not primarily a
  content/generalization failure but a **known, already-scoped shape-rule
  coverage gap** (ADR 0024/0025 recognizes only one output-shape rule).
  Extending the shape-rule detector to more transformation classes
  (crop-to-content, fixed-output-size, tiling/scaling by a train-derived
  factor) is a concrete, GPU-cheap-to-test candidate lever that was not
  visible before this diagnosis, and is arguably more promising than the
  color-swap angle since it plausibly explains a much larger fraction of
  the accuracy gap (22 tasks' worth of "far" pairs vs. up to 9 tasks
  showing a strong single-color-swap signal).
- No decision is made here on which of these two candidate levers
  (per-task color-swap correction vs. shape-rule extension) to pursue
  first, nor on continuing in-task refinement vs. investing further in
  the cross-task pretraining hypothesis (ADR 0022/0035/0036); that is
  the joint decision this ADR sets up.

## Alternatives considered

- **Re-run validation with new GPU inference to gather cleaner data**:
  rejected per explicit user instruction (no new GPU runs for this
  investigation); the persisted raw completions were sufficient to
  answer all five questions.
- **Skip grid-level reconstruction, work from the aggregate JSON only**:
  rejected; the aggregate accuracy alone cannot answer any of Q1-Q4
  (all require cell-level and grid-level comparison), and even Q5 turned
  out to hinge on task properties (`rule_holds`) not present in the
  aggregate summary.
- **Treat "far" and "close" as informal categories without pinning
  exact thresholds**: rejected; reused `validation_run_summary.py`'s
  existing thresholds (close >= 0.7, far < 0.3, `None` counts as far) to
  stay consistent with ADR 0034's own numbers rather than introducing a
  new, ADR-specific band definition.

## References

- [ADR 0022 - Hypothesis reformulation, cross-task pretraining candidate](0022-hypothesis-reformulation-post-augmentation-discovery.md)
- [ADR 0024 - Shape mismatch root cause diagnosis](0024-shape-mismatch-root-cause-diagnosis.md)
- [ADR 0025 - Deterministic shape constraint](0025-deterministic-shape-constraint.md)
- [ADR 0026 - Shape constraint at the sanity layer](0026-shape-constraint-sanity.md)
- [ADR 0028 - Timing anomaly and task complexity investigation](0028-timing-anomaly-and-task-complexity-investigation.md) (methodological precedent: reuse persisted data, no new GPU run)
- [ADR 0034 - First validation-tier run of the consolidated config](0034-first-validation-consolidated-config.md) (data source for this diagnosis)
- [ADR 0035 - Sizing the cross-task pretraining hypothesis](0035-dimensionamento-pretreino-cross-task.md)
- [ADR 0036 - Cross-task pretraining pilot](0036-piloto-pretreino-cross-task.md)
