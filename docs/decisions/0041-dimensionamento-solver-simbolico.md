# 0041 - Sizing the symbolic-solver expansion

Status: Informative

This ADR is a map before building, per ADR 0040. It measures the current
baseline's real coverage, catalogues known-relevant primitives (this
project's own plus public precedent), and proposes a search strategy and
implementation order. **No new primitive or search engine is
implemented here**; that remains a separate, future, jointly-decided
step.

## 1. Current coverage (measured, not estimated)

New script `src/evaluation/measure_baseline_coverage.py` runs the
existing `baseline_solver.solve_task` (geometry/color only, ADR 0001)
against the exact same 40-task `validation`-tier sample ADR 0034 used
for the neural solver (`select_tier_tasks(..., "validation", seed=42)`
on the evaluation split), so the two numbers are directly comparable.

Result: **0/54 held-out test pairs correct (0.0000), 0/40 tasks solved**
(`outputs/diagnostics/baseline_coverage_validation_tier.json`). This
matches the historical full-120-task evaluation-split result logged in
`docs/progress.md` (2026-09-06: 0/167 test pairs, 0%); the baseline's
only ever-recorded non-zero signal was on the *training* split
(11/1076, 1.02%), a different task distribution.

**The baseline to beat is literally 0 tasks.** Any primitive expansion
that solves even one held-out evaluation task is already a strict
improvement over the status quo, in a way the neural line never
achieved at any tier (ADR 0017 through 0039 are all 0.0000 on held-out
data too, but with far more invested effort).

## 2. Primitive catalogue

### 2a. Already implemented in this project (reusable, not to rebuild)

| Primitive | Location | Source ADR | Status |
|---|---|---|---|
| Identity/rotation/flip transforms | `src/utils/grid_ops.GEOMETRIC_TRANSFORMS` | ADR 0001 | Wired into `baseline_solver` |
| Color mapping (per-task color substitution) | `src/solvers/color_mapping.py` | ADR 0001 | Wired into `baseline_solver` |
| Shape rule: output shape equals input shape | `src/solvers/neural/shape_rule.py` | ADR 0025 | Implemented, used only as a post-process constraint on neural output, never as a standalone symbolic predictor |
| Fixed/derived output shape (per-axis: tracks input or constant, >= 3 distinct values to trust "constant") | `src/solvers/neural/fixed_shape_rule.py` | ADR 0038 | Implemented, same caveat as above, not wired into any symbolic prediction path |

Both shape rules currently only constrain a shape the neural model
already generated; they were never used to predict grid *content*
symbolically. That reuse (shape rule tells you the output size, a
content primitive fills it) is one of the cheapest available extensions
(see Section 4).

### 2b. Diagnosed but not implemented

| Primitive | Description | Source ADR | Why not yet built |
|---|---|---|---|
| Per-task dominant color-swap correction | A single color-substitution direction accounts for a mean 36% of a "close" pair's wrong cells, recurring identically across a task's own test pairs in 2/3 multi-pair cases | ADR 0037 | Named as a candidate lever, not built; detection logic sketched during diagnosis but never turned into a standalone corrector |
| Symmetry repair | Detect a grid's own symmetry (mirror/rotational) and use it to fill in or correct inconsistent regions | ADR 0037 (named for task `0934a4d8`) | Pure hypothesis, never implemented or tested |

### 2c. Public precedent (light research pass, not exhaustive)

To avoid reinventing primitive classes from scratch, per explicit
request:

- **icecuber (Kaggle ARC 2020 winner, 20.6%)**: a DSL of 142 hand-crafted
  unary grid functions, greedily composed and cached as "pieces" in a
  DAG; the winning move was less about exotic primitives and more about
  decomposing the *output* as a stack of pieces taken from the input
  (layered composition), plus aggressive caching so search stays cheap
  even with many primitives.
- **ARChitects / general public ARC-DSL practice** (2024 Prize
  runner-up paper, and DSL implementations referenced across public ARC
  solutions): primitives cluster into three families:
  - *Geometric*: translate, rotate, reflect, scale/resize, crop, tile.
  - *Color*: recolor, paint-if(condition), flood-fill, per-object
    recolor.
  - *Structural/object-based*: connected-component extraction, object
    counting, overlay/composite, mosaic/pattern completion, object
    sorting/selection (largest, most common, unique).
- Common cross-cutting idea in all public solutions surveyed: primitives
  operate over **objects** (connected components of same-colored cells),
  not only whole grids. This project's current baseline and shape rules
  are whole-grid only; object-level primitives are the single biggest
  category gap versus public precedent.

Sources: [Introducing the ARC-AGI Public Leaderboard](https://arcprize.org/blog/introducing-arc-agi-public-leaderboard), [ARC Prize 2024 Technical Report](https://arxiv.org/pdf/2412.04604), [The LLM ARChitect (da-fr/arc-prize-2024)](https://github.com/da-fr/arc-prize-2024/blob/main/the_architects.pdf).

### 2d. Catalogue summary (candidate primitive classes for this project)

1. Geometric transforms (have: identity/rotate/flip; missing: crop,
   tile/repeat, scale).
2. Color transforms (have: global color mapping; missing: conditional
   recolor, flood-fill, per-object recolor).
3. Shape derivation (have: identity-shape, fixed-shape; missing: none
   identified as cheap, content-dependent extraction stays a known gap
   per ADR 0038).
4. Object-level operations (missing entirely: connected-component
   extraction, counting, selection by property, per-object transforms).
5. Symmetry detection/repair (missing entirely, named hypothesis only).
6. Per-task color-swap correction (diagnosed, not implemented).

## 3. Search strategy (design only, not implemented)

Proposed shape, mirroring the verification discipline already used by
every accepted symbolic fix in this project (ADR 0025/0026/0038: never
trust a rule beyond what the task's own train pairs demonstrate):

1. **Primitive library**: each primitive is a pure function
   `Grid -> Grid` (or `Grid -> Optional[Grid]` for conditional ones,
   returning `None` when it does not apply), consistent with the
   existing `GEOMETRIC_TRANSFORMS` convention.
2. **Enumeration**: bounded-depth composition (start at depth 1, i.e.
   today's baseline; extend to depth 2-3 only if depth 1 proves
   insufficient), since ARC-AGI-2 was explicitly redesigned to resist
   brute-force search (per ARC Prize's own guide), so unbounded search
   depth is not expected to pay off and should not be the default
   investment.
3. **Verification gate (mandatory, before ever touching the test
   input)**: a candidate program is only accepted for a task if it
   reproduces *every* train pair's output exactly, the same all-train-
   pairs-must-fit bar `_transform_fits_all_train_pairs` already enforces
   in `baseline_solver.py`. No partial-credit or best-effort acceptance,
   matching the standing project convention.
4. **Stopping criterion**: per task, stop at the first primitive
   (or composition) that passes the verification gate against all train
   pairs; multiple predictions (up to `MAX_PREDICTIONS`, currently 2)
   are still allowed if more than one candidate passes, mirroring the
   existing submission format (ADR 0006). Across tasks, there is no
   global stopping criterion needed since each task is solved
   independently and cheaply (whole-grid/object primitives are all
   `O(grid size)` or cheaper).
5. **No learned/statistical component**: this stays a fully
   deterministic, verifiable search, consistent with Golden Rule 4 (no
   cloud LLM calls) and with keeping this line cheap to run at scale
   (240 tasks, 12h Kaggle budget, ADR 0013).

## 4. Effort and sequencing estimate

Ordered cheapest/most-validated first:

| Order | Item | Basis | Estimated effort | Rationale |
|---|---|---|---|---|
| 1 | Wire ADR 0025/0038 shape rules into `baseline_solver.py` as a *content* predictor (identity-shape + a matching content primitive, e.g. plain identity/geometric transform already covers same-shape cases) | Pure integration, both rules already implemented and tested | Cheap (hours) | Zero new logic, only wiring; may already close some of the 0/54 gap for tasks whose content transform is geometric/color but whose shape happens to also be fixed |
| 2 | Implement per-task color-swap correction (ADR 0037) as a standalone verified primitive | Detection logic already sketched in ADR 0037's diagnostic code | Cheap-medium (a day) | Existing diagnostic, just needs a corrector + train-pair verification wrapper |
| 3 | Add crop/tile geometric primitives | New primitives, same pattern as existing `GEOMETRIC_TRANSFORMS` | Medium (a day or two) | Well-understood, high-frequency primitive class in public precedent (2c), no search engine needed yet, single-primitive verified against train pairs like today |
| 4 | Add object-level primitives (connected-component extraction, counting, selection) | New subsystem, no existing code to reuse | Medium-high (several days) | Biggest category gap vs. public precedent; needs a connected-component utility first (new, small, single-responsibility module) before any object primitive can be written |
| 5 | Implement symmetry detection/repair | Pure hypothesis (ADR 0037), never prototyped | Medium (a day or two once object/grid utilities from item 4 exist) | Lower priority than object primitives since it is unvalidated even as a hypothesis |
| 6 | Bounded-depth composition search engine (Section 3, depth 2-3) | New, on top of items 1-5's primitive library | High (a week+) | Only build if single-primitive coverage (items 1-5) measurably plateaus below target; ARC-AGI-2's anti-brute-force design (2c) means this has the weakest expected payoff per effort of anything on this list |

**Recommended entry point**: items 1-3 (wiring existing rules, color-swap
correction, crop/tile) are all cheap, reuse or closely mirror code that
already exists and is tested, and can each be measured against the same
40-task validation sample (Section 1) independently, so their real
payoff becomes visible before committing to the expensive items (4-6).

## Consequences

- No code changed in `src/solvers/` by this ADR; only the new,
  standalone measurement script
  (`src/evaluation/measure_baseline_coverage.py`) and its output
  (`outputs/diagnostics/baseline_coverage_validation_tier.json`) are
  added.
- The next joint decision is which of Section 4's items to start with;
  this ADR recommends items 1-3 but does not decide for the user.
- Future implementation ADRs for each item should report their own
  measured delta against this ADR's 0/54 baseline, not a re-estimate.

## Alternatives considered

- **Start directly with the composition search engine (item 6).**
  Rejected for now: ARC-AGI-2 was explicitly redesigned against
  brute-force search, and the cheaper items (1-3) are untested, so
  building the expensive general engine first risks the same
  effort-without-validated-payoff pattern the neural line just went
  through (ADR 0040).
- **Skip measurement and estimate coverage from priors (e.g. published
  DSL solver scores).** Rejected: those scores are not comparable
  (different DSL size, different dataset version ARC-AGI-1 vs. -2,
  different task pool); a real, reproducible measurement against this
  project's own evaluation sample is cheap (one script run) and directly
  comparable to every neural-line ADR already logged.

## References

- [ADR 0001 - Solver approach selection](0001-solver-approach-selection.md)
- [ADR 0025 - Deterministic shape constraint](0025-deterministic-shape-constraint.md)
- [ADR 0034 - First validation-tier run](0034-first-validation-consolidated-config.md)
- [ADR 0035 - Sizing the cross-task pretraining hypothesis](0035-dimensionamento-pretreino-cross-task.md)
- [ADR 0037 - Error pattern diagnosis on close held-out pairs](0037-diagnostico-padrao-erro-pares-close.md)
- [ADR 0038 - Fixed output shape rule](0038-fixed-output-shape.md)
- [ADR 0040 - Priority pivot: symbolic solver becomes primary](0040-pivot-prioridade-solver-simbolico.md)
