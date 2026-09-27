# 0044 - Testing composition of existing primitives before expanding (null result)

Status: Informative

## Context

ADR 0041 items 1-2-3 (shape rules as content predictors, color-swap
correction, crop/tile) are all closed as already-exhausted on the exact
ADR 0034 40-task validation sample, each measured standalone at 0/40
(ADR 0042, ADR 0043). Before investing in the two remaining, more
expensive primitive *types* (ADR 0041 item 4, object-level/connected-
component primitives; item 5, symmetry repair), this ADR tests a
cheaper hypothesis first: does **combining** the primitives that already
exist and are already tested (`grid_ops.py` geometric transforms,
`color_mapping.py`, `crop_rules.py`, `tile_rules.py`) solve any task that
none of them solves alone?

Per explicit instruction, this is a minimal, depth-2-only composition
search (apply one primitive, then a second, on the result), not the
general bounded-depth search engine named as item 6, and not an
implementation of item 4 or item 5. The same ADR 0038 ambiguity safety
bar applies: a composition only counts if it reproduces 100% of a
task's train pairs, and if more than one distinct composition explains
the same data equally well, the task is ambiguous, never resolved by
picking one arbitrarily.

## Decision

New module `src/solvers/composition_search.py`, `find_compositions(pairs)`,
implements the depth-2 search with one explicit scope choice: **stage 1
is restricted to the 8 geometric transforms (excluding identity)**.
These are the only primitives in the library that are pure,
parameter-free functions of the input grid alone; `color_mapping.py`,
`crop_rules.py`, and `tile_rules.py` all need to see an `(input, output)`
pair to fit their parameters, which does not exist for an intermediate
stage with no known target. Stage 2 may be any of the four families,
fit against the transformed pairs `(stage1(input), output)`. Identity is
excluded from both stages: as stage 1 it reduces to the already-measured
single-primitive case; as stage 2 it reduces to a bare geometric
transform, already covered by the 0/54 baseline (ADR 0041).

Every surviving composition (one that reproduces 100% of a task's train
pairs) is verified again end-to-end as a final trust gate, mirroring the
project's standing verified-program-search discipline (ADR 0025/0026/
0038/0041 Section 3). Tests: `tests/test_composition_search.py` (5
tests, all passing), covering a genuine geometric-then-color case, a
genuine geometric-then-crop case, a no-candidate case, an ambiguous
case (constant grid, invariant under every stage-1 transform), and a
regression test confirming identity is never used as stage 1.

`src/evaluation/diagnose_composition_coverage.py` runs `find_compositions`
against the exact ADR 0034/0041/0042/0043 40-task validation sample,
pooling every surviving composition per task under the same ambiguity
bar as `diagnose_crop_tile_coverage.py`. Result:

```
validation_sample_size=40
composition_candidate=0
ambiguous=0
no_candidate=40
tasks_correct_on_held_out=0
```

Persisted at
`outputs/diagnostics/composition_coverage_validation_tier.json`.

**Zero coverage, same as every standalone primitive measured so far.**
Per the user's own stated rationale for running this test before item
4/5, this is a stronger, though not definitive, signal that this
sample's real gap is in primitive *types* not yet implemented
(object-level, symmetry), not in a lack of composition of the types
already implemented. It does not conclusively rule out deeper or wider
composition (this search is depth-2 and stage-1-restricted to geometry
by explicit design, not an exhaustive search of all composition
orderings), but it removes the cheapest version of that hypothesis as
an explanation, and does not justify prioritizing the general search
engine (item 6) next.

## Consequences

- `src/solvers/composition_search.py` exists, tested, and reusable, but
  is not wired into `baseline_solver.py` - wiring it in now would add
  code with measured 0/40 applicability on this sample, the same
  reasoning ADR 0042/0043 used to close items 1-2-3.
- ADR 0041's cheapest-first items 1-2-3, plus this depth-2 composition
  check, are now all null on the validation sample. The remaining live
  options are item 4 (object-level/connected-component primitives) and
  item 5 (symmetry repair); which to start with is an open joint call,
  not decided by this ADR.
- The general search engine (item 6) stays deprioritized: this result
  weakens, rather than strengthens, the case for building it next, since
  the cheapest form of "composition" already tested found nothing to
  compose productively with the current primitive set.
- `src/evaluation/diagnose_composition_coverage.py` and its output are
  reusable to re-check composition coverage once item 4 or item 5 adds a
  genuinely new primitive family to combine with.

## Alternatives considered

- **Allow crop/tile as stage 1 too (not just geometric transforms).**
  Rejected for this minimal version: crop/tile detection needs a known
  `(input, output)` target to fit window position or repeat factor, not
  available at an intermediate stage; supporting this would require
  exhaustively enumerating all possible crop windows/tile factors blind
  (no target to fit against), a fundamentally more expensive search that
  edges toward the general search engine (item 6) explicitly out of
  scope here.
- **Extend to depth 3.** Rejected for this minimal version, per explicit
  user instruction to bound the test to depth 2; a null depth-2 result
  is itself the signal requested before deciding whether deeper search
  is worth investing in.
- **Proceed directly to item 4 or item 5 in this same ADR.** Rejected:
  per the user's explicit framing, this ADR's job is to produce the data
  point informing that joint decision, not to make it unilaterally.

## References

- [ADR 0001 - Solver approach selection](0001-solver-approach-selection.md)
- [ADR 0038 - Fixed output shape rule](0038-fixed-output-shape.md)
- [ADR 0041 - Sizing the symbolic-solver expansion](0041-dimensionamento-solver-simbolico.md)
- [ADR 0042 - Clarifying ADR 0041 items 1-2](0042-item1-item2-clarification-color-swap-exhausted.md)
- [ADR 0043 - Measuring crop/tile coverage before building](0043-medicao-cobertura-crop-tile.md)
