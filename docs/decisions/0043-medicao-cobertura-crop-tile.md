# 0043 - Measuring crop/tile coverage before building (null result)

Status: Informative

## Context

ADR 0041 Section 4 names crop/tile primitives as item 3, the next entry
point after ADR 0042 closed items 1-2 as already-exhausted. Per the same
measure-before-build discipline used throughout this project (ADR 0035,
ADR 0041, ADR 0042), and per the explicit safety bar learned from ADR
0038 (`a32d8b75`, `38007db0`: a hypothesis is only valid for a task if it
is the *unique* explanation of all its train pairs; more than one
distinct hypothesis explaining the same data means the task is
ambiguous, never resolved by picking one arbitrarily), this ADR measures
real coverage on the exact ADR 0034/0041/0042 40-task validation sample
before writing any production primitive.

Two independent new modules implement the hypothesis families, each
using only a task's train pairs and verified against 100% of them,
mirroring `color_mapping.py`'s style:

- `src/solvers/crop_rules.py`: `FixedWindowCrop` (a constant
  `(row, col, height, width)` window, found by exhaustive search on the
  first train pair and confirmed on the rest) and `BoundingBoxCrop`
  (tightest box around non-background content, under two background
  policies: fixed color 0, or the grid's own most common color). Both
  are pure functions of the input grid alone, so they can be applied to
  a real test input, unlike "does output appear somewhere in input"
  (which presupposes the answer and cannot generalize).
- `src/solvers/tile_rules.py`: `TileRepeat`, a constant integer
  `(row_reps, col_reps)` literal-repeat factor. Reflected/alternating
  tiling is deliberately excluded, left to a future symmetry-repair
  primitive (ADR 0041 item 5) so the two primitives do not overlap.

Both are unit-tested (`tests/test_crop_rules.py`,
`tests/test_tile_rules.py`, 14 tests, all passing).

`src/evaluation/diagnose_crop_tile_coverage.py` runs both detectors
against the exact ADR 0034/0041/0042 40-task validation sample
(`select_tier_tasks(..., "validation", seed=42)`), pools every surviving
crop and tile hypothesis per task, and classifies:

- `crop_candidate` / `tile_candidate`: exactly one hypothesis in the pool.
- `ambiguous`: more than one hypothesis in the pool (e.g. two crop
  positions, or a crop and a tile hypothesis both fitting).
- `no_candidate`: the pool is empty.

## Decision

**Zero coverage, on every axis measured.**

```
validation_sample_size=40
crop_candidate=0
tile_candidate=0
ambiguous=0
no_candidate=40
tasks_correct_on_held_out=0
```

Persisted at
`outputs/diagnostics/crop_tile_coverage_validation_tier.json`.

To rule out the result being an artifact of an overly narrow detector
(rather than a real absence of crop/tile structure), a second, broader
check was run: for every task, does the output appear as a literal
contiguous substring *anywhere* in the input, in every train pair, with
no requirement that the position be derivable by a fixed rule? This is
strictly more permissive than `crop_rules.py`'s detectors (it includes,
for example, extraction of one specific object among several, which
`BoundingBoxCrop` cannot express). Result: **also 0/40 tasks.** Not one
task in this sample has its output appear as a literal sub-grid of its
input in every train pair, let alone at a consistently derivable
position. Tile coverage is 0/40 by the same measurement.

This directly corrects the framing implied by ADR 0037's earlier,
single-task manual investigation of `0934a4d8`: that task's actual
classification (ADR 0038) is "content-dependent extraction, no
derivable shape formula", not a resolved crop. The broad substring check
here confirms it is not even a literal crop in the permissive sense for
that task, or for any of the other 39.

Per the user's explicit Step 2 instruction, since coverage is
near-zero, **no crop/tile primitive is wired into `baseline_solver.py`,
and no further implementation work proceeds on this line.** The null
finding is documented here; the next step is deferred to a joint
decision, the same posture ADR 0042 took for items 1-2.

## Consequences

- `src/solvers/crop_rules.py` and `src/solvers/tile_rules.py` exist,
  tested, and reusable, but are not wired into
  `src/solvers/baseline_solver.py`. Wiring either in now would add
  code with a measured 0/40 applicability on this sample, i.e. no
  measurable improvement, the same reasoning ADR 0042 used to close
  items 1-2.
- `src/evaluation/diagnose_crop_tile_coverage.py` and its output are
  reusable if a future ADR needs to re-check crop/tile applicability on
  a different sample, or after object-level primitives (ADR 0041 item 4)
  make position-derivable extraction possible for tasks like
  `0934a4d8`.
- ADR 0041's cheapest-first order (items 1-2-3) is now fully exhausted
  on this validation sample without a single applicable primitive found.
  The remaining items are object-level (connected-component) primitives
  (item 4, most structurally novel, needs a new utility module) and
  symmetry repair (item 5), or reconsidering the general composition
  search engine (item 6) earlier than planned.

## Alternatives considered

- **Loosen crop detection to arbitrary literal sub-grid position (no
  derivability requirement), and use it anyway.** Rejected: a rule that
  can only be checked against outputs it has already seen cannot predict
  an unseen test input's crop position, so it is not a usable primitive,
  only a diagnostic pre-filter. Used here only as a broader coverage
  check (0/40), not as a candidate implementation.
- **Add reflected/alternating tiling to `tile_rules.py` now.** Deferred,
  not rejected: this overlaps with the still-unimplemented symmetry
  repair primitive (ADR 0041 item 5); keeping the two separate avoids
  duplicated logic once symmetry repair is built.
- **Proceed directly to object-level primitives (item 4) in this same
  ADR.** Rejected: per the user's explicit Step 2 conditional, a
  near-zero measurement stops the line here for a joint decision, rather
  than silently continuing to the next-cheapest item without
  confirmation.

## References

- [ADR 0001 - Solver approach selection](0001-solver-approach-selection.md)
- [ADR 0037 - Error pattern diagnosis on close held-out pairs](0037-diagnostico-padrao-erro-pares-close.md)
- [ADR 0038 - Fixed output shape rule](0038-fixed-output-shape.md)
- [ADR 0041 - Sizing the symbolic-solver expansion](0041-dimensionamento-solver-simbolico.md)
- [ADR 0042 - Clarifying ADR 0041 items 1-2](0042-item1-item2-clarification-color-swap-exhausted.md)
