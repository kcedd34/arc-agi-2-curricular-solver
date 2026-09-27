# 0038 - Fixed output shape rule

## Status

Informative.

## Context

ADR 0037 found that of the 22 "far" held-out pairs, 18 fail because they
belong to tasks where `output_shape_equals_input_shape` (ADR 0024/0025)
does not hold, and named "shape-rule extension to more transformation
classes" as a candidate cheap lever, alongside per-task color-swap
correction, without deciding between them.

Per explicit user instruction, this ADR investigates extending the shape
rule, using only train pairs (no GPU run), starting from the 18 far
pairs / 13 distinct tasks where `rule_holds=False`:
`0934a4d8`, `13e47133`, `269e22fb`, `2b83f449`, `38007db0`, `45a5af55`,
`4c3d4a41`, `71e489b6`, `800d221b`, `898e7135`, `8698868d`, `a32d8b75`,
`bf45cf4b` (18 far pairs, since `13e47133`/`2b83f449`/`4c3d4a41`/`71e489b6`
each contribute more than one far pair).

### Classification pass across the 13 tasks

Checked, from train pairs only, whether each task's size relation fits a
clean crop (literal exhaustive submatch of input), tile (integer-multiple
exact block repetition), or rescale (integer-ratio uniform block value)
pattern:

| Category | Count |
|---|---|
| Crop (literal submatch) | 0 |
| Tile (exact block repetition) | 0 |
| Rescale (uniform block value) | 0 |
| Other | 13 |

None of the three categories originally hypothesized in ADR 0037's
framing exist in this sample. This is a real correction to that framing,
reported before any implementation. A closer look at "other" split it
further:

| Sub-pattern | Tasks | Count |
|---|---|---|
| Fixed output shape (constant or simple per-axis rule) | `269e22fb`, `38007db0`, `a32d8b75` | 3 |
| Unreliable 2-point linear fit (train pairs too few to fit a formula with any confidence) | `45a5af55`, `8698868d`, `898e7135`, `bf45cf4b` | 4 |
| Content-dependent extraction, no derivable shape formula | `0934a4d8`, `13e47133`, `2b83f449`, `4c3d4a41`, `71e489b6`, `800d221b` | 6 |

Only the first sub-pattern, "fixed output shape", offers a
train-pairs-only, 100%-consistency-checkable signal comparable in rigor
to the existing ADR 0025 rule. The other two sub-patterns are explicitly
not pursued in this ADR (see Consequences).

### Detection design: asymmetric per-axis rule

For each axis (rows, columns) independently, across a task's train
pairs:

- If the output value always equals the input's own value on that axis,
  the axis resolves to **"tracks input"**. This is the same identity
  relationship ADR 0025 already trusts for the whole-shape case, so no
  additional evidence is required, even if the input never varied along
  that axis.
- Else, if the output value is the same constant across every train
  pair, the axis resolves to **"always this constant"**, but only when
  the input's value on that axis took **at least 3 distinct values**
  across train pairs while the output stayed put. Real disconfirming
  variation is required before accepting "constant" over the cheaper
  "tracks input" default.
- Else the axis is **unresolved**, which rejects the whole task.

Both axes must resolve for the task to receive a rule
(`resolve_fixed_output_shape`, `src/solvers/neural/fixed_shape_rule.py`).
Implementation kept small, matching the `shape_rule.py`/
`shape_constraint.py` pattern; `target_shape_for` applies a resolved rule
to a new input, producing the `(target_rows, target_cols)` pair
`force_grid_shape` (unchanged, ADR 0025) already expects.

### Why the distinct-value threshold is 3, not 2

The first implementation used "input varied at all" (>= 2 distinct
values) as the bar for accepting "constant", by direct analogy with the
existing rule's own evidentiary standard. Against synthetic unit tests
this reproduced the intended pattern (`269e22fb` included, `38007db0`
included, `a32d8b75` excluded). But checking each of the three candidate
tasks against their own real held-out test data (not just synthetic
tests) surfaced a genuine problem:

- `269e22fb` (5 train pairs, rows take 4 distinct values, columns take 3
  distinct values, output always (20, 20)): both held-out test pairs
  match the predicted shape exactly.
- `a32d8b75` (3 train pairs, input shape never varies at all, output
  always (20, 24)): correctly returns no rule (rows and columns both
  fail the variation requirement), matching the user's explicit
  exclusion decision from genuine ambiguity ("output columns are always
  24" and "output columns are input columns minus 6" are indistinguishable
  with zero data points of column variation).
- `38007db0` (2 train pairs, rows never vary, columns take exactly 2
  distinct values (19, 25), output columns always 7): structurally
  passes the >= 2-distinct-values bar, but **empirically false**. One of
  its two real held-out test pairs needs 8 columns, not 7. With only one
  pair of differing inputs to compare, a coincidental match ("both of
  the 2 examples I happened to see used 7 columns") is exactly as likely
  as a genuine invariant, and the held-out data confirms it was
  coincidental here.

This is a concrete illustration of small-n structural verification's
limit: passing a structural ambiguity check is necessary but not
sufficient, since n=2 differing inputs cannot distinguish "always this
constant" from "constant only in the examples I've seen so far". Per
explicit user decision, the fix is not a one-off exclusion of
`38007db0` by task id, but a generalizable tightening of the detection
criterion: require **at least 3** distinct input values before accepting
the constant hypothesis on that axis. This is stricter than the
identity-tracking case (which still requires zero extra evidence,
consistent with ADR 0025) but gives the constant hypothesis a
meaningfully harder bar to clear than "any variation at all", trading
away `38007db0`'s coverage (which turned out to be wrong) while keeping
`269e22fb`'s (which holds up against real data on both of its axes: 4
and 3 distinct values respectively) and continuing to reject `a32d8b75`
(0 distinct values, fails by an even wider margin).

### Real payoff, smaller than initially hypothesized

ADR 0037's framing speculated the shape-rule-extension lever could reach
up to 18 far pairs. After this investigation, the real, validated
payoff is:

- **1 task, `269e22fb`, 2 held-out test pairs.** Both pairs' predicted
  shape (20, 20) matches the expected shape exactly.
- `38007db0` (2 pairs) and `a32d8b75` (3 pairs) are both excluded, for
  two different reasons (empirical falsification vs. structural
  ambiguity respectively), not implemented.
- The 6 content-dependent extraction tasks (`0934a4d8`, `13e47133`,
  `2b83f449`, `4c3d4a41`, `71e489b6`, `800d221b`) and the 4 unreliable
  2-point-linear-fit tasks (`45a5af55`, `8698868d`, `898e7135`,
  `bf45cf4b`) remain a documented known gap, not pursued in this ADR.

## Decision

Implement `resolve_fixed_output_shape`/`target_shape_for`
(`src/solvers/neural/fixed_shape_rule.py`), covering only `269e22fb` in
validated scope. Do not implement crop/tile/rescale detection (absent
in this sample) or content-dependent extraction (no derivable
train-pairs-only formula). Do not wire this rule into the production
pipeline (`per_attempt_conditional_mitigation_pair_diagnostics.py`) in
this ADR; that remains a separate integration decision.

### Test results

Unit tests (`tests/test_fixed_shape_rule.py`, 7/7 passing):
- Resolves a constant-shape rule when input varies (>= 3 distinct
  values per axis) and output does not (`269e22fb`-shaped case).
- Resolves a mixed rule (rows track input, columns fixed) when columns
  clear the 3-distinct-value bar.
- Returns `None` when only 2 distinct input values back the constant
  hypothesis (`38007db0`'s exact real pattern, kept as a permanent
  regression test with the real task's own train-pair shapes).
- Returns `None` when input never varies at all (`a32d8b75`'s exact
  real pattern, also kept as a permanent regression test).
- Returns `None` when neither axis hypothesis holds.
- `target_shape_for` applies both a constant rule and an
  input-tracking rule correctly to a new input.

Smoke test on `269e22fb`, using real persisted task data and raw
completions (`data/ARC-AGI-2/data/evaluation/269e22fb.json`,
`outputs/raw_generations/validation_consolidated_config/evaluation/`):

| Measure | Result |
|---|---|
| Predicted shape matches expected shape, both held-out test pairs | Yes, 2/2 |
| `per_cell_accuracy`: `None` -> real value | Yes: test pair 0 attempts 0.5075/0.4675; test pair 1 attempts 0.0/0.0 |
| `exact_match` appears | No, 0/4 attempts |
| No false positive on `a32d8b75` | Confirmed: returns `None` |
| No false positive on `38007db0` | Confirmed: returns `None` (with the 3-distinct-value threshold) |

The two 0.0 accuracies on test pair 1 show the shape fix alone does not
guarantee content correctness, consistent with every prior ADR in this
chain (ADR 0025-0027, 0034): fixing shape is necessary but not
sufficient for `exact_match`.

Regression check against the full 120-task evaluation split (broader
than the 40-task validation sample): zero new tasks incorrectly gain a
rule, the only new coverage beyond the existing `output_shape_equals_input_shape`
rule is `269e22fb`, and every task where the existing rule already holds
continues to resolve consistently under the new rule (both axes track
input, matching the existing rule's own behavior exactly, not a
conflicting result).

No further "sanity"-tier run (8-task sample) was performed: with only
one validated task in scope, the smoke-tier check against `269e22fb`'s
own real held-out data already constitutes the available evidence,
reusing persisted data with no new GPU run, consistent with ADR 0028's
and ADR 0037's own reused-data methodology. A `validation`-tier run
remains the bar for any future policy/architecture decision per Golden
Rule 7, not reached or claimed here.

## Consequences

- `fixed_shape_rule.py` is implemented and tested but not integrated
  into the production diagnostic pipeline. Wiring it in (e.g. as a
  second, narrower gate alongside `output_shape_equals_input_shape` in
  `per_attempt_conditional_mitigation_pair_diagnostics.py`) is a
  separate, small follow-up decision, not made here.
- The real payoff of this lever is materially smaller than ADR 0037's
  initial framing speculated: 1 task / 2 held-out pairs, not up to 18.
  This does not invalidate ADR 0037's Q5 finding (close vs. far still
  tracks shape-rule coverage almost perfectly); it clarifies that most
  of the remaining coverage gap is content-dependent extraction, not a
  cheaply detectable shape formula.
- The **3-distinct-input-values threshold** (`MIN_DISTINCT_INPUTS_FOR_CONSTANT`
  in `fixed_shape_rule.py`) is now a documented, load-bearing constant,
  not an arbitrary choice: it is the direct result of `38007db0`'s
  empirical falsification, and any future change to it should be
  re-validated against `38007db0`'s and `a32d8b75`'s train-pair shapes
  (kept as permanent regression tests) before being applied.
- The 6 content-dependent extraction tasks and the 4 unreliable
  2-point-linear-fit tasks are a documented known gap. No shape formula
  derivable from train pairs alone was found for either group in this
  investigation; per-task color-swap correction (ADR 0037's other named
  candidate lever) remains undecided and unimplemented.
- No decision is made on pursuing tile/rescale detection further (this
  sample simply does not contain any clean examples of either), on
  implementing content-extraction detection, or on the standing choice
  between further in-task refinement and cross-task pretraining
  (ADR 0022/0035/0036).

## Alternatives considered

- **Accept `38007db0` with a documented risk, rather than excluding it**:
  this was the initially recommended option (the structural criterion
  is defensible and the measured effect on the task's own persisted raw
  completions happened to cause no harm, since that pair's completions
  were already shape-garbled regardless of the constraint). Rejected per
  explicit user decision: a rule known to be empirically false in
  general should not be shipped merely because it happened not to hurt
  in one observed instance, especially when a small, principled
  criterion change removes the problem without special-casing.
- **Guard the rule with an additional "only apply if it does not reduce
  accuracy" runtime check, keeping `38007db0` conditionally**: not
  pursued; it would make the rule's behavior depend on having ground
  truth at prediction time, which is not available for real test-only
  inference, defeating the purpose of a train-pairs-only detection
  rule.
- **Pick an even higher distinct-value threshold (4 or 5) for extra
  safety margin**: rejected as unjustified by any evidence; 3 is the
  smallest change that resolves the concrete `38007db0` counter-example
  while still admitting `269e22fb` (which clears 3 distinct values on
  both axes with real margin, 4 and 3 respectively). Raising it further
  would only reduce coverage without a countervailing signal from any
  known counter-example.
- **Implement a 2-point linear-formula fit for the 4 "unreliable"
  tasks**: attempted informally during classification
  (`linear_formula` helper); rejected as unreliable, since a line
  through exactly 2 points is unfalsifiable from train data alone (any
  2 points admit a unique line, so "the fit is good" carries no
  information) - the same class of problem `38007db0` demonstrated
  concretely.

## References

- [ADR 0024 - Shape mismatch root cause diagnosis](0024-shape-mismatch-root-cause-diagnosis.md)
- [ADR 0025 - Deterministic shape constraint](0025-deterministic-shape-constraint.md)
- [ADR 0026 - Shape constraint at the sanity layer](0026-shape-constraint-sanity.md)
- [ADR 0037 - Error pattern diagnosis on "close" held-out pairs](0037-diagnostico-padrao-erro-pares-close.md) (source of the shape-rule-extension lever and the 18-far-pair framing this ADR corrects)
