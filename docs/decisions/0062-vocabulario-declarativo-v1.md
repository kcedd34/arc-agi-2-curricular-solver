# 0062 - Declarative-step vocabulary v1

Status: Accepted (2026-09-21)

## Context

Per [ADR 0061](0061-curriculum-restart.md), UC04 (Stage 0) needs a
declarative-step vocabulary before `src/curriculum/spec/vocabulary.py`
and `src/curriculum/spec/interpreter.py` can be implemented: RN-CUR-01
requires the vocabulary to become an ADR before implementation, and the
PRD's own desk-check requirement (RN-CUR-14) requires every accepted
solution to be expressible as a short, human-traceable sequence of
declarative steps, independent of how many named primitives the library
accumulates over time.

This ADR was blocked for five autonomous cycles by a misreading of
RN-CUR-01 as requiring prior user approval before drafting it. The user
resolved this via RN-CUR-27/RN-CUR-28 (see ADR 0061 decision item 6):
recording this ADR with Status Accepted is itself the decision, not a
pending request. The user also gave explicit authorization to adopt the
vocabulary v1 proposal below as a starting point and to adjust it during
implementation if a real problem is found, recording the adjustment
here, without seeking approval first.

## Decision

### Design principle

The vocabulary stays deliberately small and grows much more slowly than
the primitive library. Named library primitives (e.g. `rotate_90`,
`tile_3x3`, `largest_object`) are defined as fixed sequences of
vocabulary steps, not as new vocabulary operations. This keeps desk-check
traces independent of how large the primitive library gets (RN-CUR-14):
a human checking a solution's trace only ever needs to know this small,
stable operation set, never the growing catalog of named primitives
built from it. The primitives/operations ratio is tracked in
`docs/curriculum/learning-curve.md` as a health indicator; a ratio that
stops growing (primitives added without reuse of existing operations)
is a signal the vocabulary may need a new version, not that it should
grow ad hoc.

### Operations (v1)

| Operation | Signature | Meaning |
|---|---|---|
| `bind` | `bind(name, value)` | Names a value (grid, region, count, scalar) for reuse in later steps. |
| `shape_out` | `shape_out(rows, cols)` | Declares the output grid's shape before emitting cells into it. |
| `partition` | `partition(source, kind)` | Splits a grid into a list of regions. `kind` is one of `cells`, `rows`, `cols`, `blocks(h, w)`, `objects(connectivity, background)`, `color_layers`. |
| `correspond` | `correspond(list_a, list_b, by)` | Pairs elements of two partitions. `by` is one of `index`, `position`, `color`, `size_rank`. |
| `for_each` | `for_each(list, body)` | Applies a step sequence (`body`) to every element of a partition. |
| `test` | `test(predicate, value)` | Evaluates a named predicate against a bound value or region, producing a boolean. |
| `branch` | `branch(condition, then_steps, else_steps)` | Conditional execution of one of two step sequences. |
| `emit` | `emit(region, source)` | Writes a region into the output grid. `source` is `copy` (copy a bound region's cells) or `fill(color)` (fill with a constant color). |
| `transform` | `transform(region, op)` | Applies a geometric/color operation to a region, producing a new region. `op` is one of `rotate(k)`, `flip(axis)`, `transpose`, `recolor(map)`, `crop_to_content`. |
| `compose` | `compose(default_color)` | Finalizes the output grid, filling any cell never written by `emit` with `default_color`. |

### Predicates

`is_background(cell_or_region)`, `color_eq(a, b)`, `color_in(color,
set)`, `count_eq(list, n)`, `size_gt(region, n)`,
`touches_border(region, grid)`, `is_largest(region, list)`,
`is_smallest(region, list)`.

### Expressions

Integer arithmetic only, over `in.rows`, `in.cols`, partition counts,
and previously `bind`-named values (e.g. `in.rows * 3`, `count(objects)
- 1`). No loops, no arbitrary function calls, no access to anything not
reachable through `bind`/`partition`/`test`. This keeps every expression
mechanically re-evaluable during a desk check without executing code.

### Trace schema

Every executed step is recorded as one trace entry:

```
{
  "step": <int, 1-based index>,
  "op": <operation name>,
  "region": <region/grid identifier the op acted on, or null>,
  "condition": <predicate result, for test/branch, or null>,
  "result": <bound name or region produced, or null>,
  "value": <scalar/grid value produced, or null>
}
```

A full solution trace is the ordered list of these entries, from the
first `bind`/`partition` of the input to the final `compose`.

### Worked example: `007bbfb7`

Specification (block-tiling: for each non-background input cell, place
a copy of the whole input grid at the corresponding 3x3 block position;
otherwise leave the block as background):

```
1. bind(g_in, input)
2. shape_out(g_in.rows * 3, g_in.cols * 3)
3. partition(g_in, cells) -> cell_list
4. for_each(cell_list, [
     test(color_eq(cell, bg), is_bg)
     branch(is_bg,
       then: [ emit(block_at(cell.row, cell.col), fill(bg)) ],
       else: [ emit(block_at(cell.row, cell.col), copy(g_in)) ]
     )
   ])
5. compose(bg)
```

Caveat: `bg = 0` is a constant bound value used only to make this
example concrete for the interpreter's acceptance test. The real
hypothesis-learner (Stage 1 onward) must infer the background color
from the task's own demonstration pairs, never hardcode it; this
constant does not appear in `spec/vocabulary.py` or
`spec/interpreter.py` outside the test fixture built from this example.

This specification is the interpreter's acceptance test
(`tests/curriculum/spec/test_interpreter.py`): executing it against
`007bbfb7`'s real train pairs must reproduce every training output
exactly.

### Governance

- **Versioning.** This is v1. A future v2 (or later) is a new ADR, not
  a silent edit to this one, unless RN-CUR-27 applies (an
  implementation-level adjustment discovered during Stage 0-6 work,
  recorded as an amendment here rather than a new ADR, the same
  mechanism ADR 0061 used for RN-CUR-27/RN-CUR-28 itself).
- **Bar for adding an operation.** A new operation must (a) be
  justified as atomic and general, not a shortcut for one specific
  primitive, (b) have at least 2 plausible, distinct uses across
  different task shapes, and (c) ship with a unit test in
  `tests/curriculum/spec/`.
- **Forbidden pattern.** No operation may be added that, alone,
  reproduces an entire named primitive end to end (e.g. no single
  `tile_3x3_by_content(...)` operation); primitives must stay expressed
  as sequences of the smaller operations above.
- **Tracking.** `docs/curriculum/learning-curve.md` records, at each
  checkpoint, the count of named library primitives versus the count of
  vocabulary operations in use; this ratio is expected to grow over
  time as evidence the vocabulary is staying small relative to what it
  expresses.

## Consequences

- `src/curriculum/spec/vocabulary.py` implements the operations,
  predicates, and expression grammar above as data/callable
  definitions; `src/curriculum/spec/interpreter.py` executes a step
  sequence against a `Grid` input and produces the trace schema above.
- `outputs/curriculum/state.json`'s `blocked_on` field (citing this
  ADR) is cleared now that it exists.
- Stage 1 (solving `007bbfb7` for real, using only its demonstration
  pairs) can only begin once the interpreter's acceptance test (the
  worked example above) passes against real data.
- Any future adjustment to this vocabulary found necessary during
  implementation is recorded as an amendment to this ADR (RN-CUR-27),
  not as silent drift between this document and the code.

## Alternatives considered

- **A large, primitive-oriented vocabulary** (one operation per named
  transformation, e.g. `tile_3x3`, `mirror_repeat`, `object_recolor` as
  first-class vocabulary operations). Rejected: this is exactly the
  shape RN-CUR-14's desk-check requirement exists to avoid - the
  vocabulary would grow in lockstep with the primitive library instead
  of staying smaller than it, making a human trace no easier to verify
  than reading the primitive's own implementation, and defeating the
  purpose of having a separate declarative layer at all.
- **A general-purpose DSL** (arbitrary control flow, user-defined
  functions, unrestricted expressions, closer to a small programming
  language than a fixed operation set). Rejected: this reopens exactly
  the failure mode the induce-verify-apply program-induction line hit
  and closed under the prior approach (ADR 0060, k=6 and k=96 both
  Abandon) - an unconstrained language is harder to search, harder to
  desk-check by hand (RN-CUR-14 again), and gives no structural
  guarantee that a "solution" is actually built from reusable,
  traceable pieces rather than an opaque one-off script.
