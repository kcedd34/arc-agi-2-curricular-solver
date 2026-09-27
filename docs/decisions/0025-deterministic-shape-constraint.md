# 0025 - Deterministic shape constraint for mechanically derivable output sizes

## Status

Informative (smoke-tier evidence only, per Golden Rule 7; not adopted as
the default solver behavior yet).

## Context

ADR 0024 found the shape-mismatch gap from ADR 0023 is not caused by a
hard size rule, by copying a training-pair size, or by the token cap: 7
of 8 sampled tasks have an output size rule at least as simple as "output
shape equals input shape", and the model's EOS emission is premature or
inconsistent specifically in the row-count dimension (row width was
correct in 18/22 kept predictions, row count almost never was).

Since the "output shape equals input shape" rule is directly verifiable
from a task's own train pairs, with no model or GPU involved, this gap
can be closed deterministically for the tasks where that rule holds,
without waiting for the model to learn to stop at the right row count.

## Decision

Implement and smoke-test a shape-forcing constraint gated by a
mechanical rule check:

1. **Rule detection** (`src/solvers/neural/shape_rule.py`,
   `output_shape_equals_input_shape(task)`): true only if every train
   pair's output shape (rows, cols) exactly equals its own input shape.
   A single counter-example rejects the rule for that task. Pure logic,
   no GPU dependency, host-tested (`tests/test_shape_rule.py`).
   Deliberately scoped to only this one rule; a fixed-shape-regardless-
   of-input rule or a partial rule (rows follow input, columns fixed,
   as seen in `136b0064`) are left for a future extension.

2. **Shape-forcing post-process** (`src/solvers/neural/shape_constraint.py`,
   `force_grid_shape(grid, target_rows, target_cols)`): truncates extra
   rows/columns beyond the target, and pads missing rows/columns by
   repeating the last existing row/value. Chosen as the simplest total
   function that never raises, even on an empty grid. Padding by
   repetition is a placeholder, not a claim about correct content: ADR
   0024 already showed content is wrong regardless of shape, so this
   step is about making the shape correct, not about guessing the
   missing cells' values. Host-tested (`tests/test_shape_constraint.py`).

3. **Gating**: the constraint is applied only when
   `output_shape_equals_input_shape(task)` is true for that task. When
   false (e.g. `0934a4d8`), predictions pass through unchanged, keeping
   the current EOS-dependent behavior, since that case needs
   content-dependent reasoning this fix does not attempt.

4. **Single-pass measurement** (`src/evaluation/shape_constraint_diagnostics.py`):
   `generate_with_counts` runs once per pair; both the unconstrained
   (current behavior) and constrained readings are computed by
   post-processing the same raw predictions two different ways. No
   extra GPU/model calls beyond a normal smoke run.

## Smoke test

Ran on 2 tasks from ADR 0024's "output = input shape" group, chosen for
showing a clean row-count-only undershoot on their held-out test pair
with no column-width issue: `135a2760` and `1818057f`
(`src/evaluation/run_shape_constraint_smoke.py`, evaluation split).

| Task | Rule holds | Split | Pair | Unconstr. shape | Unconstr. exact | Constr. shape | Constr. exact |
|---|---|---|---|---|---|---|---|
| 135a2760 | yes | train | 0 | yes | no | yes | no |
| 135a2760 | yes | train | 1 | yes | no | yes | no |
| 135a2760 | yes | test | 0 | **no** | no | **yes** | no |
| 1818057f | yes | train | 0 | yes | no | yes | no |
| 1818057f | yes | train | 1 | yes | no | yes | no |
| 1818057f | yes | train | 2 | yes | no | yes | no |
| 1818057f | yes | test | 0 | **no** | no | **yes** | no |

Both held-out test pairs, the ones that actually needed the fix, flip
from shape mismatch to shape match once the constraint is applied. The 5
training pairs already had the correct shape unconstrained (as expected,
they are in-distribution for TTT), and the constraint is a no-op there.

`exact_match` stays "no" everywhere, constrained or not. This is the
expected outcome, not a failure of this fix: ADR 0024 already established
generation reaches the right shape and content is separately wrong; this
change only removes the shape gate so a future content fix's
`exact_match` reading will not be blocked by shape alone.

## Consequences

- Confirms, on n=2 (smoke-tier), that the row-count EOS problem ADR 0024
  diagnosed is deterministically fixable for tasks with the simplest
  shape rule, with no model change and no retraining.
- This is smoke-tier evidence (Golden Rule 7): sufficient to confirm the
  mechanism works as designed, not sufficient on its own to adopt this
  as the solver's default behavior. A `sanity`-layer run (8 tasks) is
  the natural next check, extending to `13e47133`, `142ca369`,
  `16de56c4` (which also have the rule confirmed per ADR 0024, some with
  overshoot rather than undershoot patterns) and confirming `0934a4d8`
  correctly stays unconstrained.
- Does not decide the ADR 0022 content-lever choice (color augmentation
  vs. cross-task pretraining). That decision should come after a
  `sanity`- or `validation`-layer `exact_match` reading is available with
  shape corrected, per the user's explicit instruction that this fix is
  orthogonal to and should precede that choice.
- `136b0064`'s partial rule (rows follow input, columns fixed at 7) and
  `16b78196`'s fixed-shape rule are not covered by this constraint yet;
  extending `shape_rule.py` to recognize them is a candidate follow-up,
  not scheduled here.

## Alternatives considered

- **Constrain generation directly (e.g. a custom `StoppingCriteria` or
  logits processor that forces EOS at the right row)**: more invasive,
  couples the fix to the sampling loop, and is harder to unit-test in
  isolation from the model. Post-processing the decoded grid achieves
  the same outcome with pure, host-testable functions and no generation
  API changes.
- **Pad missing rows/columns with a fixed value (e.g. background color 0)
  instead of repeating the last row/value**: equally simple, but
  repeating the last row/value was chosen as a marginally better guess
  for tasks where trailing rows are often uniform or a background color
  in ARC-AGI-2 grids; either choice is a placeholder since content
  correctness is not this fix's goal.
- **Run generation twice per pair (once to measure current behavior,
  once with constraint applied during decoding)**: unnecessary GPU cost;
  post-processing the same single-pass predictions two ways gives an
  equivalent comparison for a shape-only constraint.
