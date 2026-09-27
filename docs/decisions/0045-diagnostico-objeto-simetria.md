# 0045 - Cheap diagnostic for object/component and symmetry-repair heuristics (null result)

Status: Informative

## Context

ADR 0041's cheapest-first items 1-2-3, plus the depth-2 composition check
in ADR 0044, are all closed at 0/40 on the exact ADR 0034/0041/0042/0043
40-task validation sample. The only remaining live options are item 4
(object-level/connected-component primitives) and item 5 (symmetry
repair), both materially more expensive to build than anything measured
so far. Per explicit instruction, before committing to a full build of
either, this ADR measures both cheaply with narrow, hand-written
heuristics against train pairs only, to avoid repeating the "build first,
measure later" pattern the project has otherwise avoided since ADR 0041.

Same ADR 0038 safety bar as every prior diagnostic: a heuristic only
counts as a task-level candidate if it reproduces 100% of that task's
train pairs, and if more than one distinct hypothesis explains the same
data equally well, the task is ambiguous, never resolved by picking one
arbitrarily.

## Decision

**Diagnostic 1 (object/connected-component, item 4).** New module
`src/solvers/connected_components.py` provides shared flood-fill utility
(`connected_regions`, `find_color_components`, `bounding_box`,
`crop_to_bbox`, 4- or 8-connected). New module `src/solvers/object_heuristics.py`
defines `ObjectHeuristic(background, connectivity, selection)`, a
12-variant cross-product (2 backgrounds ["zero", "most_common"] x 2
connectivities [4, 8] x 3 selections ["largest", "rarest_color",
"most_frequent_shape"]). Each variant crops to the selected component's
bounding box, keeping the grid's original values inside that box (no
masking of non-component cells). `detect_object_heuristics(pairs)` pools
every variant that reproduces 100% of a task's train pairs.

**Diagnostic 2 (symmetry break-and-repair, item 5).** New module
`src/solvers/symmetry_heuristics.py` defines
`SymmetryHeuristic(symmetry, region_index, form)`: compares a grid to its
own transform under 3 symmetry kinds (horizontal mirror, vertical mirror,
180-degree rotation), finds the mismatch mask's connected regions, and
tolerates up to 2 regions (not exactly 1) because all 3 transforms are
involutions, so a genuine one-sided anomaly structurally produces
mismatches on both sides. `region_index` (0 or 1) selects which region,
`form` ("as_found" or "repaired") selects whether the crop reads straight
from the input or from the transformed grid. 12 variants total (3
symmetries x 2 region indices x 2 forms). `detect_symmetry_heuristics(pairs)`
pools every variant that reproduces 100% of a task's train pairs.

Both families are unit-tested (`tests/test_connected_components.py`,
`tests/test_object_heuristics.py`, `tests/test_symmetry_heuristics.py`,
14 tests total, all passing), including explicit no-candidate and
ambiguous-case tests. Full project suite: 234 passed.

`src/evaluation/diagnose_object_symmetry_coverage.py` runs both families
independently against the exact ADR 0034/0041/0042/0043/0044 40-task
validation sample, applying the ADR 0038 ambiguity bar per family per
task. Result:

```
validation_sample_size=40
object:    {'candidate': 0, 'ambiguous': 0, 'no_candidate': 40}, tasks_correct_on_held_out=0
symmetry:  {'candidate': 0, 'ambiguous': 0, 'no_candidate': 40}, tasks_correct_on_held_out=0
```

Persisted at
`outputs/diagnostics/object_symmetry_coverage_validation_tier.json`.

**Zero coverage for both diagnostics, the same null pattern as every
primitive family measured since ADR 0042.** This does not prove item 4 or
item 5 would fail as full engines (both diagnostics are deliberately
narrow - 12 hand-picked variants each, not a general search over
segmentation or symmetry-repair strategies), but it removes the cheap
version of both hypotheses as an explanation for this sample's gap, and
gives no evidence favoring one over the other as the next build target.

## Consequences

- `connected_components.py`, `object_heuristics.py`, and
  `symmetry_heuristics.py` exist, tested, and reusable, but are not wired
  into `baseline_solver.py` - same reasoning as ADR 0042/0043/0044, wiring
  in code with measured 0/40 applicability on this sample adds nothing.
- Neither diagnostic gives evidence for prioritizing item 4 over item 5
  or vice versa; the choice of which (if either) to build as a full
  engine, or whether to look at a different task family/sample instead,
  remains an open joint call, explicitly not decided by this ADR.
- `connected_components.py` is a genuinely reusable low-level utility
  (not heuristic-specific) - any future full object-level primitive build
  would likely start from it rather than reimplementing flood-fill.
- `src/evaluation/diagnose_object_symmetry_coverage.py` and its output
  are reusable to re-check coverage if either heuristic family is
  broadened later (e.g. masking non-component cells to background, or
  allowing 3+ mismatch regions under a different symmetry-break model).

## Alternatives considered

- **Build the full connected-component segmentation engine or the full
  symmetry-repair engine directly.** Rejected per explicit user
  instruction: measure cheaply first, given the project's now-repeated
  pattern of near-zero coverage on this sample, before spending on a
  materially larger implementation.
- **Mask non-component cells to background in object heuristics, instead
  of keeping original grid values inside the bounding box.** Rejected for
  this diagnostic: adds a second axis (mask vs. keep) to an
  already-12-variant search, and the "keep original values" choice is at
  least as permissive a superset for detecting any bounding-box-shaped
  output.
- **Tolerate more than 2 mismatch regions in the symmetry heuristic.**
  Rejected: beyond 2 regions there is no principled way to decide which
  subset is "the anomaly" without turning this into exactly the kind of
  general search the item 5 engine would need to do properly; 3+ regions
  is treated as no candidate for this cheap diagnostic.

## References

- [ADR 0001 - Solver approach selection](0001-solver-approach-selection.md)
- [ADR 0038 - Fixed output shape rule](0038-fixed-output-shape.md)
- [ADR 0041 - Sizing the symbolic-solver expansion](0041-dimensionamento-solver-simbolico.md)
- [ADR 0042 - Clarifying ADR 0041 items 1-2](0042-item1-item2-clarification-color-swap-exhausted.md)
- [ADR 0043 - Measuring crop/tile coverage before building](0043-medicao-cobertura-crop-tile.md)
- [ADR 0044 - Testing composition of existing primitives before expanding](0044-composicao-primitivas-existentes.md)
