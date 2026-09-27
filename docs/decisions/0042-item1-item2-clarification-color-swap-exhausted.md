# 0042 - Clarifying ADR 0041 items 1-2: no new content mechanism, color-swap already exhausted

Status: Informative

## Context

Before picking an entry point among ADR 0041 Section 4's ordered items,
a direct code-level question was raised: does item 1 ("wire ADR 0025/0038
shape rules into `baseline_solver.py` as a content predictor") actually
generate grid *content*, or does it just fall back to a trivial case
already covered by the 0/54 baseline measurement? And if item 1 has no
real content mechanism, item 2 (a pure, from-scratch, exact color-swap
primitive, distinct from ADR 0037's partial/residual finding) was named
as the next candidate, with an explicit requirement: it only counts as a
new primitive if it is verified against 100% of a task's train pairs,
not a dominant-with-noise pattern.

## Decision

**Item 1, confirmed hollow.** `src/solvers/neural/shape_rule.py`'s
`output_shape_equals_input_shape` returns a `bool`; `src/solvers/neural/
fixed_shape_rule.py`'s `resolve_fixed_output_shape` returns a `(rows_rule,
cols_rule)` shape tuple. Neither produces a grid. Wiring "item 1" as
ADR 0041 itself describes ("identity/geometric transform already covers
same-shape cases") means falling back to `identity` in
`src/utils/grid_ops.GEOMETRIC_TRANSFORMS` whenever shape matches, i.e.
predicting "output = input". That is exactly the trivial fallback
already present in `baseline_solver.py` and already included in the
0/54 measurement (ADR 0041 Section 1). Item 1 contributes nothing new.

**Item 2, unexpectedly already implemented and already measured at
zero.** `src/solvers/color_mapping.py` (`infer_color_mapping` /
`apply_color_mapping`, from ADR 0001) already is the requested
primitive: it requires identical shape between input and output, builds
a color-to-color substitution by comparing corresponding cells
position-by-position across every train pair, and rejects (`None`) the
moment any inconsistency appears, with no partial-credit acceptance. It
is already wired into `baseline_solver.predict_test_input` (lines
38-42) and was therefore already part of the 0/54 measurement.

To confirm this rather than assume it, a new diagnostic script,
`src/evaluation/diagnose_color_mapping_coverage.py`, ran
`infer_color_mapping` against the exact ADR 0034/0041 40-task validation
sample (`select_tier_tasks(..., "validation", seed=42)`):

```
validation_sample_size=40
tasks_with_exact_global_color_mapping=0
tasks_where_mapping_alone_correct_on_held_out=0
```

Persisted at
`outputs/diagnostics/color_mapping_coverage_validation_tier.json`.

**Not one of the 40 tasks even has a valid mapping.** This is a stronger
result than "0 correct": the primitive never reaches a candidate
prediction on this sample, so building a new, separately-named module
with the same logic would duplicate already-tested code and add nothing
measurable. Item 2, as literally specified (global, value-based, exact
across all train pairs), is exhausted.

Per explicit user decision, this line is closed here rather than
building a broader color-swap variant (e.g. position-dependent mapping)
or resurrecting ADR 0037's partial/residual pattern as a full generator.
The next entry point is ADR 0041 Section 4 item 3 (crop/tile geometric
primitives), which has no existing implementation to check against
first.

## Consequences

- No change to `src/solvers/baseline_solver.py` or
  `src/solvers/color_mapping.py`; both already contain the logic that
  was being considered as "new".
- New diagnostic script `src/evaluation/diagnose_color_mapping_coverage.py`
  and its output are added, reusable if a future ADR needs to re-check
  color-mapping applicability on a different sample.
- ADR 0041's items 1 and 2 are both closed as non-viable entry points on
  this sample, not because they were tried and failed, but because they
  were already tried (by earlier ADRs) and already failed. The real next
  build step is item 3.

## Alternatives considered

- **Build item 2 anyway, as a new module.** Rejected: it would be
  functionally identical to `infer_color_mapping`/`apply_color_mapping`,
  already measured at 0/40 applicable on this exact sample; this would
  not be a new primitive, only new code with the same behavior.
- **Build a position-dependent (non-global) color mapping instead.**
  Deferred, not rejected outright: raised as an option but not chosen;
  a per-cell-position mapping is closer to memorizing exact output
  coordinates than to a generalizable "color swap" rule, and was not
  prioritized over item 3's already-catalogued, well-understood
  primitive class (crop/tile).
- **Formalize ADR 0037's partial/dominant color-swap as a full-grid
  generator.** Deferred, not rejected outright: would need a different
  safety bar than "100% of the transformation must be explained by one
  mapping", since ADR 0037's finding was explicitly partial (mean 36% of
  wrong cells); not pursued now per explicit user decision to move to
  item 3 instead.

## References

- [ADR 0001 - Solver approach selection](0001-solver-approach-selection.md)
- [ADR 0025 - Deterministic shape constraint](0025-deterministic-shape-constraint.md)
- [ADR 0037 - Error pattern diagnosis on close held-out pairs](0037-diagnostico-padrao-erro-pares-close.md)
- [ADR 0038 - Fixed output shape rule](0038-fixed-output-shape.md)
- [ADR 0040 - Priority pivot: symbolic solver becomes primary](0040-pivot-prioridade-solver-simbolico.md)
- [ADR 0041 - Sizing the symbolic-solver expansion](0041-dimensionamento-solver-simbolico.md)
