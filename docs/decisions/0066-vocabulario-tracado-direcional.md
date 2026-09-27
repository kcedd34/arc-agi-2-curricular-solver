# 0066 - Directional tracing vocabulary additions (Seed step, IsIsolated predicate, SegmentTo region)

Status: Accepted
Date: 2026-09-21

## Context

Task 3 (`docs/curriculum/tasks/ded97339.md`), concept `draw_or_extend_lines`,
subtype `ligar_pontos_mesma_cor`. RN-CUR-31's exhaustion evidence (see that
file) proves the current v2 declarative vocabulary (`spec/vocabulary.py`,
`spec/interpreter.py`) has three concrete gaps for this task:

1. No layout produces a same-size canvas pre-seeded as a copy of the
   input; `block_grid` always produces `shape_out = in_shape * scale` by
   tiling copies of the whole input, and `_exec_compose` only ever fills
   remaining `None` cells with one flat `default_color`.
2. No selector tests a single input cell's own local neighborhood
   (orthogonal isolation) at 1:1 granularity; existing selectors classify
   block-grid/`IndexGrid` elements, not raw input cells directly.
3. No `Region`/`EmitSource` can address a dynamically discovered span of
   cells between two runtime-resolved coordinates; `Region = Union[
   RegionRef, BlockAt]` and `EmitSource = Union[Copy, Fill]` only ever
   address a single fixed block or named region.

Per RN-CUR-31 (ADR 0064), new vocabulary is only added once existing
pieces are proven insufficient, and per the standing project governance
bar (CLAUDE.md, [Standing instruction] plus BOOTSTRAP.md's ADR-before-
vocabulary convention), a new *vocabulary* addition (not just a new
*library piece* built from existing vocabulary) needs its own ADR with
evidence that each addition is atomic, general, and has at least two
plausible uses.

## Decision

Add three small, atomic vocabulary primitives:

1. **`Seed(source: Expr)` step.** Initializes `env.output_grid` from a
   real grid's cells (e.g. a copy of the task's own input) before any
   `Compose`/`Emit` steps run, instead of leaving it as all-`None` until
   `_exec_compose`'s flat-fill fallback. Atomic: it does exactly one
   thing, pre-fill the canvas. General: any same-size, in-place-edit task
   benefits, not just line drawing.
2. **`IsIsolated(grid, row, col)` predicate**, paired with the existing
   but previously-unused `Cells()` `PartitionKind` (already declared in
   `spec/vocabulary.py`, never consumed by any piece until now). True
   when the cell at `(row, col)` is non-background and has no
   orthogonally-adjacent cell of the same color. Atomic: a single boolean
   test, no side effects. General: the "isolated marker cell" concept
   recurs across the `draw_or_extend_lines` family.
3. **`SegmentTo(from_row, from_col, direction)` region.** Resolved at
   interpret time by walking from `(from_row, from_col)` one cell at a
   time along `direction` until either the grid border or the first
   non-background cell is reached; yields the strictly-between span if
   the terminating cell satisfies a caller-supplied stop predicate (e.g.
   "same color as origin"), otherwise resolves to an empty region so
   `Emit` writes nothing. Atomic: one resolution rule, direction plus a
   stop predicate. General: parametrizing the stop predicate covers
   multiple subtypes without new vocabulary per subtype.

## Plausible uses (governance bar: at least 2 each)

- `Seed`: (a) this task, (b) any of the other same-size probe-pool tasks
  already flagged in `docs/curriculum/learning-curve.md`'s structural-
  incompatibility count, most of which need an in-place edit over an
  otherwise-unchanged canvas rather than a block-tiling transform.
- `IsIsolated`: (a) this task's origin selector, (b) a future
  `raio_ate_borda`/`raio_ate_obstaculo` task, both of which also start a
  ray from an isolated marker cell (probe-pool examples `1bfc4729`/
  `1d398264`, `342ae2ed`/`52df9849`, not implemented now, cited only as
  the second plausible use).
- `SegmentTo`: (a) this task's same-color-partner stop predicate, (b) the
  same `raio_ate_borda`/`raio_ate_obstaculo` subtypes, which need the same
  walk-until-condition mechanics with a border-reached or first-obstacle
  stop predicate instead of a same-color-partner one.

## Consequences

- `spec/vocabulary.py` gains one new `Step` variant (`Seed`), one new
  `Region` variant (`SegmentTo`), and the `Cells()` `PartitionKind`
  becomes reachable by at least one selector piece for the first time.
- `spec/interpreter.py` needs a `_exec_seed` handler and a `SegmentTo`
  resolver alongside the existing `BlockAt` resolver.
- `search/compose.py`/`search/params.py` need to enumerate the new
  layout/selector/content combination; this must not remove or alter any
  existing `block_grid`-based composition path, so `007bbfb7` and
  `00576224` keep solving unchanged (regression-checked per RN-CUR-30
  before this ADR's implementation is considered done).
- No change to `loader.py`'s `Task`/`TrainPair` structures or to the
  probe/evaluation gabarito-access restrictions (RN-CUR-03/RN-CUR-05).
