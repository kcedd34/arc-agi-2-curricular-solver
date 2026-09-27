# Learning curve (probe pool)

Per RN-CUR-17: after each acceptance, probe-pool coverage is measured without
intervention and recorded with the library version. This file records the
curve's points (v0 through v3 so far), each produced by a real CLI execution
(`python -m src.curriculum.cli probe`) in a fresh process, per RN-CUR-30.

## Methodology

- **Probe pool size (N):** 200 tasks, fixed by `docs/curriculum/partition.json`
  (`probe_pool_size: 200`, seed `20260921`).
- **Coverage metric:** `num_exact_match_tasks / num_tasks` as computed by
  `src/curriculum/probe.py::run_probe_checkpoint`, using the same
  `search_task` engine curricular selection uses (RN-CUR-05/RN-CUR-03
  compliant: only `probe.py` and `evaluator/solutions.py` read probe-pool
  test outputs).
- **Library version:**
  - **v0 (empty):** the `REGISTRY` with zero primitives registered.
    Produced for this baseline only, by temporarily commenting out the single
    import line in `src/curriculum/library/primitives/__init__.py`
    (`from src.curriculum.library.primitives import tiling`), running `probe`
    in a fresh subprocess, then restoring the file to its exact original
    content and re-running the full test suite (90 passed) as a sanity check.
    This is the exact "empty REGISTRY" state the bug diagnosed before this
    session's acceptance work started.
  - **v1:** the `REGISTRY` as of the `007bbfb7` acceptance, containing
    exactly one primitive, `block_tile_by_background`.
  - **v2:** the composition-based library after
    `docs/curriculum/tasks/stage-3-prep.md` steps 1-3 (RN-CUR-33): one
    layout piece (`block_grid`, unified factor-per-axis), two selector
    pieces (`input_cell_not_background`, `row_parity`), three content
    pieces (`copy`, `fill`, `flip`), plus pre-enumeration pruning
    (per-axis scale, palette, layout/selector structural compatibility).
    Search now enumerates layout x selector x content compositions
    instead of whole-primitive names (`src/curriculum/search/compose.py`).
  - **v3 (current):** task 3 (`ded97339`) added new vocabulary (`Seed`
    step, ADR 0066) and 4 new pieces: layout `identity_canvas`
    (same-size canvas seeded from the input), selector `isolated_point`
    (per-cell orthogonal-isolation test), content `draw_lines`/`keep`
    (directional scan to a same-color isolated partner). Corrected from
    an earlier "stays v2" call in this session: the decisor's own rule
    is that any new piece bumps the version, regardless of whether the
    surrounding composition architecture (layout x selector x content)
    itself changed.
- **Primitives/vocabulary-operations ratio:** number of primitives registered
  in `REGISTRY` divided by the number of distinct `Step` kinds declared in
  `src/curriculum/spec/vocabulary.py`'s `Step` union (`Bind`, `ShapeOut`,
  `Partition`, `Correspond`, `ForEach`, `Test`, `Branch`, `Emit`,
  `Transform`, `Compose`, 10 kinds). This definition is not fixed elsewhere
  in the project; it is stated here explicitly for auditability, since the
  governing prompt's phrase has no prior formula in the codebase to anchor
  to.

## Curve points

| Date | Library version | Primitives/pieces | Vocabulary step kinds | Ratio | Probe pool (N) | Exact-match tasks | Accuracy |
|---|---|---|---|---|---|---|---|
| 2026-09-21 | v0 (empty, pre-`007bbfb7`) | 0 | 10 | 0.00 | 200 | 0 | 0.0000 |
| 2026-09-21 | v1 (post-`007bbfb7`, `block_tile_by_background`) | 1 | 10 | 0.10 | 200 | 0 | 0.0000 |
| 2026-09-21 | v2 (post-stage-3-prep steps 1-3, composition search) | 6 (1 layout + 2 selectors + 3 content) | 10 | 0.60 | 200 | 3 | 0.0150 |
| 2026-09-21 | v3 (post-task-3/`ded97339`, ADR 0066) | 10 (2 layout + 3 selectors + 5 content) | 11 (`Seed` added, ADR 0066) | 0.91 | 200 | 3 | 0.0150 |
| 2026-09-21 | v4 (post-task-4, `SegmentTo.stop_condition`, ADR 0068) | 10 (2 layout + 3 selectors + 5 content, `draw_lines` gains a `stop_condition` parameter, no new piece) | 11 (unchanged, `stop_condition` is a field on existing `SegmentTo`, not a new `Step`/`Region` kind) | 0.91 | 200 | 3 | 0.0150 |
| 2026-09-22 | v5 (post object-pack promotion, ADR 0071/0072) | 25 (main library 10 unchanged: 2 layout + 3 selectors + 5 content; object pack adds 15: 2 layout + 7 selectors + 6 content, `docs/curriculum/library.md`) | 11 (unchanged: ADR 0071's additions - `Objects` under `PartitionKind`, `RecolorObject`/`Erase`/`FillBbox`/`Translate` under `TransformOp`, `SlideTo` under `Region`, 8 new predicates under `Predicate` - are all sub-variants of existing `Step`-level unions, not new top-level `Step` kinds) | 2.27 | 200 | 4 | 0.0200 |
| 2026-09-23 | v7 (Rodada 1 do ciclo continuo, poda fill_color/background, ADR 0075) | 25 (inalterado: nenhuma peca nova, apenas um parametro de escrita renomeado - `fill_content`'s `background`->`fill_color` - e a fonte de candidatos de um parametro de deteccao existente - `_background_candidates` - trocada de uniao para intersecao) | 11 (inalterado) | 2.27 | 200 | 5 | 0.0250 |

Report format (BOOTSTRAP.md Section 9.4/10): `Curva de aprendizado (pool
sonda): 0/200 -> 0/200 -> 3/200 -> 3/200 -> 3/200 -> 4/200 de 200`.

## Interpretation

Coverage stayed flat from v0 to v1 (0/200 both), then moved for the first
time at v2: 3/200 (`67a3c6ac`, `6fa7a44f`, `cce03e0d`). Corrected after a
per-task validation against the real desk-check compositions and train/test
shapes (`docs/curriculum/desk-checks/{67a3c6ac,6fa7a44f,cce03e0d}.md`,
generated for this validation since no desk check had been persisted for
probe-pool tasks before): only one of the three, `67a3c6ac`, is the
degenerate same-size case. The other two are genuine, non-degenerate
compositions, not whole-grid flips in disguise:

- **`67a3c6ac`** (in/out shapes 7x7, 4x4, 6x6, all same-size): `block_grid`
  with `scale_rows=scale_cols=1` produces a single block covering the whole
  grid; `row_parity` on a one-block-row layout is trivially always "even",
  so `selected_content` (`flip`, axis horizontal) always fires and
  `not_selected_content` never executes. Confirmed, not assumed: 7 verified
  candidates were persisted, differing only in `not_selected_content`
  (`copy`, `fill` at 4 different colors, `flip` on both axes), all agreeing
  on every train and test pair. Since an unexecuted branch cannot
  distinguish between those 7 choices, this is genuinely the degenerate
  single-block case, equivalent to an unconditional whole-grid horizontal
  flip. Coherent with the task, not coincidental, for the part that
  actually runs (`flip`).
- **`6fa7a44f`** (in 3x3, out 6x3, NOT same-size): `block_grid` with
  `scale_rows=2, scale_cols=1` lays out 2 real block-rows, each sized 3x3.
  `row_parity` genuinely discriminates here: block-row 0 (even) gets
  `copy`, block-row 1 (odd) gets `flip` (axis vertical). Both branches
  execute and are load-bearing on all 4 train pairs and the test pair (1
  verified candidate only, no ambiguity). The rule is "stack the input on
  top of its own vertical mirror" - a real 2-block composition, not a
  disguised flip.
- **`cce03e0d`** (in 3x3, out 9x9, NOT same-size): `block_grid` with
  `scale_rows=scale_cols=3` (9 real blocks, each sized 3x3), same fractal
  arrangement family as `007bbfb7`. Selector `input_cell_not_background`
  with `background=2` (not `007bbfb7`'s `background=0`): where the
  same-position input cell equals the background, the block gets `copy`
  (fractal copy of the whole input); elsewhere it gets `fill` with color 0.
  Both branches execute on real, non-trivial masks across all 3 train pairs
  and the test pair (1 verified candidate, no ambiguity). This is a genuine
  reuse/generalization of the `007bbfb7` mask-fractal family to a different
  background color and a swapped copy/fill assignment, not a new layout
  family and not a coincidence.

Net correction: of the 3 solved probe-pool tasks, exactly 1
(`67a3c6ac`) is same-size and degenerate; the other 2 are expanding-layout
compositions (one a new 2-block stack pattern, one a direct generalization
of the already-solved `007bbfb7` family). No accidental-match risk beyond
the ordinary ADR 0038 ambiguity bar (each composition's `not_selected`
branch that does execute was checked as a single verified candidate, or as
multiple candidates that only vary in genuinely unexecuted code, not an
enumeration bug). Desk-check artifacts for these 3 tasks were persisted for
this validation only (`docs/curriculum/desk-checks/`,
`outputs/curriculum/desk-checks/`); `probe.py` and `evaluator/solutions.py`
remain the only modules that read probe-pool gabaritos during normal
search/selection (RN-CUR-05); this validation additionally used
`desk-check-persist`, an existing RN-CUR-30 audit tool, in the same
gabarito-reading role it already has for curricular tasks.

### Structural-incompatibility count (stage-3-prep step 5's own question)

Measured directly (`enumerate_compositions(task)` called on every probe-pool
task, real read of `docs/curriculum/partition.json`'s `probe_pool` and the
real task files, not a re-derivation): **0/200** probe-pool tasks are
structurally incompatible with the current library in the sense of "no
composition enumerable at all". This is because `row_parity` has no
structural eligibility precondition (`search/compose.py`'s
`_selector_eligible` only restricts `input_cell_not_background`), so
`block_grid x row_parity x (any content pair)` is always enumerable
regardless of the task's own shapes - the pruning added in step 3 narrows
*which* compositions get tried, it never yet empties the candidate set
entirely for any task in this pool.

This means the real "same-size layout" bottleneck named in
`stage-3-prep.md` step 4 does not show up as "zero compositions", it shows
up as "compositions exist but none verify against the train pairs". For
scale, **137/200 (68.5%)** of probe-pool tasks have `out_shape == in_shape`
on every train pair - the same layout-family gap the prior near-miss
analysis (`docs/curriculum/tasks/00576224.md`) already flagged. Corrected
count (see per-task validation above): only **1 of those 137** is solvable
today (`67a3c6ac`, the degenerate same-size case, `scale=1` collapsing to a
whole-grid flip). The other 2 solved probe-pool tasks (`6fa7a44f`,
`cce03e0d`) are NOT same-size and fall outside this 137-task bucket
entirely; they were solved by genuine expanding-layout compositions
(`scale_rows=2` stacking, and the `007bbfb7` mask-fractal family reused
with `background=2`), unrelated to the same-size gap. The remaining 136
same-size tasks need an in-place, cell-level edit rule (recolor, fill,
line-drawing, object move, symmetry completion) that no current content
piece expresses, since every content piece (`copy`/`fill`/`flip`) still
operates on a whole `BlockAt` region, not per-cell.

Both v0/v1 checkpoints (unchanged from the prior session) and the new v2
checkpoint are recorded as real entries in `outputs/curriculum/state.json`'s
`probe_pool_checkpoints` list, produced by genuine fresh-process CLI
executions, per RN-CUR-30.

Raw CLI output:
- v0: `Probe checkpoint 2026-09-21: 0/200 exact match (accuracy=0.0000, solved=0)`
- v1: `Probe checkpoint 2026-09-21: 0/200 exact match (accuracy=0.0000, solved=0)`
- v2: `Probe checkpoint 2026-09-21: 3/200 exact match (accuracy=0.0150, solved=3)`
- v3 (post-task-3): `Probe checkpoint 2026-09-21: 3/200 exact match (accuracy=0.0150, solved=3)`
- v4 (post-task-4): `Probe checkpoint 2026-09-21: 3/200 exact match (accuracy=0.0150, solved=3)`

## Scale test: 5 largest training-set tasks, v5 (post object-pack promotion), no teaching

Per object-pack.md Section 5.7: same method as the earlier v2 scale test
below (frozen library, no new pieces, no pruning changes, 5 largest
training-set tasks by total cell count, real `search_task` execution per
task in a fresh process, RN-CUR-30), rerun after the object pack's
promotion to the main library (v5, ADR 0072) to see whether the pack
generalizes to hard tasks with no additional teaching.

| Task | Shape (all pairs) | Object-pack candidates | Search time | Solved | Closest hypothesis |
|---|---|---|---|---|---|
| `b74ca5d1` | 30x30, same-size | 5000 (capped) | 71.891s | No | `identity_canvas + input_cell_not_background(bg=4) + draw_lines(bg=9,any_obstacle)/draw_lines(bg=3,any_obstacle)` (cell_similarity=0.920) |
| `f9d67f8b` | 30x30, same-size | 5000 (capped) | 72.214s | No | `identity_canvas + input_cell_not_background(bg=6) + draw_lines(bg=9,any_obstacle)/draw_lines(bg=9,any_obstacle)` (cell_similarity=0.956) |
| `05a7bcf2` | 30x30, same-size | 5000 (capped) | 52.219s | No | `identity_canvas + input_cell_not_background(bg=4) + draw_lines(bg=0,same_color_isolated)/draw_lines(bg=0,any_obstacle)` (cell_similarity=0.750) |
| `264363fd` | 30x30, same-size | 5000 (capped) | 84.688s | No | `identity_canvas + input_cell_not_background(bg=8) + draw_lines(bg=3,any_obstacle)/draw_lines(bg=2,any_obstacle)` (cell_similarity=0.916) |
| `753ea09b` | 30x30, same-size | 5000 (capped) | 96.205s | No | `block_grid(1,1) + row_parity + copy/copy` (cell_similarity=0.803) |

Still 0/5, same tasks and same overall bottleneck as the pre-promotion v2
run: all 5 remain same-size 30x30 with no per-cell local content piece
(object-pack content pieces still write into a selected object's region,
not an arbitrary scattered cell subset) able to express their edit rule.
Every task now hits the object pack's own `MAX_COMPOSITIONS_PER_TASK`
enumeration cap (5000), confirming the pack's search space is still large
on 30x30 grids even after Section 6's inventory-based pruning. Absolute
per-task time (52.2s-96.2s) is well above the Section 5.8 probe-pool
sample average (26.93s/task combined main+object search) because these
are the 5 largest training-set tasks by construction, not a
probe-pool-representative sample; this is a separate data point, not a
re-measurement of the 1.335x risk ratio (still the governing figure,
below the 5x threshold). Full detail:
`outputs/curriculum/scale-test-v5-detail.txt`.

## Highlights: transfers vs. degenerate case (decisor request, turn 2)

Of the 3 solved probe-pool tasks documented above, exactly 2 are genuine
transfers of a taught concept to a new task, and 1 is degenerate:

- **Genuine transfer 1 (taught concept: `row_parity` selector, 2-block
  stacking):** `6fa7a44f`. Both branches of `row_parity` execute and are
  load-bearing on every pair (`copy` on even block-rows, `flip` vertical on
  odd block-rows), producing a real 3x3 -> 6x3 expansion. Not seen verbatim
  in training; the selector class generalizes to a task the library was
  never shaped around.
- **Genuine transfer 2 (taught concept: `input_cell_not_background`
  mask-fractal, the `007bbfb7` family):** `cce03e0d`. Same 3x3 fractal
  arrangement as `007bbfb7`, but with `background=2` (not `007bbfb7`'s `0`)
  and the copy/fill assignment swapped between the mask's two sides. This is
  the mask-fractal concept surviving a change in background color and
  branch assignment, not a coincidental match.
- **Degenerate case:** `67a3c6ac`. `block_grid` collapses to a single
  1x1 block, which makes `row_parity` always "even" and its
  `not_selected_content` branch dead code; the 7 verified candidates only
  differ in that unreachable branch. The rule that actually runs is an
  unconditional whole-grid horizontal flip, equivalent to no selector at
  all.

## Task 3 (`ded97339`) probe checkpoint: no transfer observed

After task 3's pieces (`identity_canvas`, `isolated_point`,
`draw_lines`/`keep`, built on `Seed`/`IsIsolated`/`SegmentTo`, ADR 0066)
were implemented and accepted, a real `cli probe` run over the same
200-task probe pool produced the v3 row above: 3/200, unchanged from v2.
This is not just the same count by coincidence: a direct re-check
(`search_task` run against every probe-pool task in a fresh process)
confirms the solved set is exactly the same 3 tasks as v2
(`67a3c6ac`, `6fa7a44f`, `cce03e0d`); none of them use the new pieces,
and no other probe-pool task newly verifies.

This is a genuine degenerate/no-transfer result, not a bug: task 3's own
`draw_or_extend_lines` concept (`ligar_pontos_mesma_cor` subtype) is a
narrow one, requiring the exact combination of same-size canvas,
per-cell isolation, and directional same-color-partner scanning. None of
the 137 same-size probe-pool tasks flagged in the "Structural-incompatibility
count" section above happen to match this specific subtype closely enough
to newly verify. This is consistent with `ded97339.md`'s own selection
rationale (chosen for being the simplest curricular-pool instance of a
narrow subtype, not for probe-pool breadth) and is the expected shape of
early curricular progress: each task's pieces are proven general only in
the sense of "at least 2 plausible future uses" (ADR 0066's own governance
bar), not "solves other probe-pool tasks today". The other 2 subtypes
`isolated_point`/`SegmentTo` were justified against
(`raio_ate_borda`/`raio_ate_obstaculo`) are not yet implemented; they
remain candidate future tasks that would exercise the same primitives with
a different stop predicate.

## Scale test: 5 largest training-set tasks, v2 frozen, no teaching

Per the decisor's request (turn 2): before starting task 3, the frozen v2
library (no new pieces, no pruning changes) was run against the 5 largest
tasks in the training split (by total cell count across all train/test
grids; training split only, never evaluation). This measures how far v2
already reaches on hard, real tasks with no additional teaching.

Method: real execution of `search/compose.py::enumerate_compositions` and
`spec/interpreter.py::run` in a fresh process (RN-CUR-30), via a throwaway
diagnostic script (`tmp_scale_test.py`, deleted after this record was
written). "Hypotheses after pruning" is the current production candidate
count (RN-CUR-33 step 3 pruning active). "Hypotheses before pruning" was
measured by monkeypatching `search/params.py`'s
`infer_consistent_axis_scale`/`infer_palette` and `search/compose.py`'s
`layout_matches_input_dims` to always fall back to the full unpruned range,
re-running the same enumeration, then restoring the originals; this never
modified the checked-in pruning code. "Closest hypothesis" is the
candidate (verified or not) with the most train pairs matched exactly,
tie-broken by cell-level similarity on the pair it fails; task-level
"solved" additionally checks the verified candidate's test prediction
against the real training-set test output (safe to read directly for
training-set tasks, unlike probe/evaluation gabaritos, RN-CUR-03/05).

| Task | Shape (all pairs) | Hypotheses after pruning | Hypotheses before pruning | Search time | Solved | Closest hypothesis train-pair hits | Closest hypothesis |
|---|---|---|---|---|---|---|---|
| `b74ca5d1` | 30x30, same-size | 169 | 5000 (capped) | 0.0005s | No | 0/3 | `block_grid(1,1) + row_parity + copy/copy` |
| `f9d67f8b` | 30x30, same-size | 144 | 5000 (capped) | 0.0004s | No | 0/4 | `block_grid(1,1) + row_parity + copy/copy` |
| `05a7bcf2` | 30x30, same-size | 49 | 5000 (capped) | 0.0003s | No | 0/3 | `block_grid(1,1) + row_parity + copy/copy` |
| `264363fd` | 30x30, same-size | 100 | 5000 (capped) | 0.0003s | No | 0/3 | `block_grid(1,1) + row_parity + copy/copy` |
| `753ea09b` | 30x30, same-size | 121 | 5000 (capped) | 0.0003s | No | 0/3 | `block_grid(1,1) + row_parity + copy/copy` |

"Before pruning" hits `MAX_COMPOSITIONS_PER_TASK = 5000` (the enumeration
cap) for all 5 tasks: the unpruned parameter space (full 1..10 scale range
on both axes, full 0-9 background palette) is large enough on its own,
before even considering that these are same-size tasks where the correct
scale (1) is already the cheapest guess. Pruning does not change whether
these tasks are solved, only how fast the search discards the same wrong
branches; the real bottleneck is expressiveness, not search cost.

None of the 5 solved: all are same-size (30x30 on every pair, confirming
these sit inside the 137/200-style same-size bucket already flagged
above), all have a moderate number of changed cells relative to total
cells (31 to 285 of 900), and the input/output color palettes are almost
identical (identical or one added color). The closest hypothesis in every
case is the degenerate `block_grid(1,1) + row_parity + copy/copy`
composition, i.e. an unconditional identity copy: it scores non-trivial
cell similarity (0.68 to 0.96) purely because most of the 900 cells are
unchanged, but 0 exact train-pair matches, because it changes nothing.

Missing piece in every case: a **per-cell local content operation**, not a
whole-`BlockAt` one. All 3 current content pieces (`copy`, `fill`, `flip`)
write into an entire block region; none can leave most of a same-size
canvas untouched while editing a scattered subset of cells (recolor,
line/ray drawing, symmetry completion). This is the same gap already
named in the "Structural-incompatibility count" section above (136
same-size probe-pool tasks) and is exactly the gap task 3's
`draw_or_extend_lines` concept is chosen to start closing: `05a7bcf2` in
particular introduces a new output color (`3`) not present in any input,
consistent with a drawn/added line or marker rather than a recolor of
existing content.

## Task 4 (`SegmentTo` stop_condition generalization, ADR 0068) probe checkpoint: no transfer observed

Task 4's diagnostic (`outputs/curriculum/task4-diagnostic.md`) found that 7
of 10 sampled `draw_or_extend_lines` probe-pool tasks (subtypes
`raio_ate_borda`, `raio_ate_obstaculo`) fail because `SegmentTo` only
supports one stop rule. Per RN-CUR-31, `SegmentTo` was generalized (not
duplicated into new per-subtype regions) with a `stop_condition` field
supporting 3 values: `same_color_isolated` (unchanged default), `border`,
`any_obstacle` (ADR 0068). `search/params.py` now enumerates all 3 values
as candidates for `draw_lines`'s `stop_condition` parameter, wired through
`library/pieces/content.py` and `spec/_regions.py`'s
`_resolve_segment_to`/`_resolve_obstacle_stop`/`_resolve_border_stop`.

Regression stayed green throughout (RN-CUR-16/RF09): `python -m
src.curriculum.cli validate` reports 3/3 (`007bbfb7`, `00576224`,
`ded97339`), `Schema errors: 0`, `Regressions: 0`. This required one
in-scope side fix: adding `stop_condition` candidates exposed a latent
gap where `draw_lines` could be paired with `block_grid` even though it
reads the loop element's own `(row, col)` as a real input coordinate,
valid only under `identity_canvas`'s `Cells()` partition; this was
harmless with a single stop_condition value (coincidental shape match on
`007bbfb7`) but became a real train/test disagreement once `border` was
added. Fixed with `_content_eligible` in `search/compose.py`, gating
`draw_lines` to `identity_canvas` only (same precondition already used
for the `isolated_point` selector).

A real `cli probe` run over the same 200-task probe pool after this
change produced the v4 row below: 3/200, unchanged from v3. A direct
re-check (`search_task` run against every probe-pool task in a fresh
process, status only, no test-output reads) confirms the solved set is
still exactly the same 3 tasks as v2/v3 (`67a3c6ac`, `6fa7a44f`,
`cce03e0d`); none of the 7 named task-4 anchors newly solve.

This is a genuine no-transfer result, not a bug, and was diagnosed
directly on train pairs only (RN-CUR-03/RN-CUR-05: `task.train` read for
the 7 named tasks, `task.test[i].output` never read or printed for them;
`search_task`'s own train-pair-only verification is the sole source of
the "no_candidate" status below):

- `d037b0a7`: the real rule fires in a single fixed direction (down) from
  each isolated marker, not `draw_lines_content`'s unconditional 4
  directions; adding `border` alone still produces spurious fills in the
  other 3 directions, so no composition verifies against all train pairs.
- `1bfc4729`: the actual output is a rectangular frame drawn around each
  marker's row/column band, not a ray to the border; a different concept
  from `SegmentTo` entirely.
- `1d398264`: shows diagonal/connecting patterns between marker clusters,
  also outside `SegmentTo`'s straight orthogonal-ray model.
- `97999447`: shows a periodic dash-fill pattern extending from the
  marker, not a simple ray-to-border or ray-to-obstacle fill.
- `342ae2ed`, `52df9849`, `e5790162` (`raio_ate_obstaculo` anchors): use
  multi-cell rectangular markers (per the task-4 diagnostic), which the
  `isolated_point` selector (single isolated cell only) never selects as
  an origin in the first place, independent of `stop_condition`.

Per RN-CUR-31 discipline, none of these gaps (direction-selectivity,
frame-drawing, diagonal/dash patterns, multi-cell origin selection) are
folded into this task's scope: they are documented here as open,
candidate future generalizations, each needing its own exhaustion
evidence before new vocabulary or pieces are added.

Raw CLI output (v4): `Probe checkpoint 2026-09-21: 3/200 exact match
(accuracy=0.0150, solved=3)`.

## Probe checkpoint v5 (post object-pack promotion): first new probe-pool transfer since v2

Per object-pack.md Section 5.6, a real `cli probe`-equivalent run
(`src/curriculum.probe_checkpoint_detail`, same `run_probe_checkpoint`
engine, fresh process, RN-CUR-30) over the same 200-task probe pool
after the object-pack promotion (v5) produced 4/200, up from 3/200 at
v2/v3/v4. A direct diff against the v4 solved set (`67a3c6ac`,
`6fa7a44f`, `cce03e0d`) confirms all 3 remain solved and exactly one new
task newly verifies: **`23b5c85d`**.

Desk-checked (`cli desk-check-persist 23b5c85d`,
`docs/curriculum/desk-checks/23b5c85d.md`): 6 verified candidates, all
of the shape `layout=crop_to_selected_object(connectivity,
single_color=True, background) selector=smallest_object
content=crop_content`, agreeing on trace vs. implementation on all 5
train pairs and the test pair in every case. The 6 candidates differ
only in `connectivity` (4 or 8) and `background` (0, 2, or 3); this is
expected, benign ambiguity (none of those 3 background values or either
connectivity choice changes how this particular grid segments into
objects), not the `b1948b0a`-style coincidence (there is no
`selected_content == not_selected_content` pair here at all: the crop
layout has a single content arm, `crop_content`, with no complementary
branch to collapse). This is a genuine transfer of the object-pack
concepts marked `coberto` earlier in this same round
(`segmentacao_4`/`segmentacao_8`, `objeto_tamanho`, `recorte`) to a
probe-pool task never taught to or seen by the library: "crop the
smallest object out of the grid."

This desk check also surfaced and fixed a real bug (documented as a
correction in [ADR 0072](../decisions/0072-promocao-do-pacote-de-objetos.md)):
`desk_check/persist.py::build_hypothesis_record` had not received the
same `ObjectComposition` type-dispatch adapter that
`desk_check/run.py::_trace_step_counts` got during the promotion, so
persisting this task's desk check initially raised `KeyError:
'crop_to_selected_object'`. Fixed by mirroring the same dispatch in
`persist.py`; `tests/curriculum` suite verified green (243 passed)
after the fix.

Raw CLI output (v5): `Probe pool: 200 tasks / Solved: 4 / Exact match: 4
/ Elapsed: 2333.4s (11.67s/task)`. Full detail:
`outputs/curriculum/probe-checkpoint-v5-detail.txt`.

## Probe checkpoint v6 (post ADR-0073 correction, 2026-09-22)

[ADR 0073](../decisions/0073-correcao-solved-vs-unanime.md) separated
`solved` (gabarito match, two-attempt policy) from `unanimous`
(candidate agreement), since the old `status == "solved"` never checked
the gabarito. The probe pool was re-run in full under the corrected
`compute_verified_verdict` (`src/curriculum/probe.py`, real `cli probe`
execution, not a re-derivation from the v5 numbers).

Raw CLI output (v6): `Probe checkpoint 2026-09-22: 4/200 solved
(gabarito-verified), accuracy=0.0200, unanimous=4`. `num_unanimous == 4
== num_solved`: the 4 probe-pool tasks unanimous among verified
candidates (`23b5c85d`, `67a3c6ac`, `6fa7a44f`, `cce03e0d`, the same set
as v5) are all genuinely gabarito-correct, with no false positive in
this pool analogous to the 3 reverted curricular tasks. The probe-pool
honest baseline is unchanged by the correction: **4/200 (2%)**.

## Probe checkpoint v7 (Round 1 of the continuous cycle, pruning package, ADR 0075, 2026-09-23)

Real `cli probe` execution after the Round 1 pruning package (`fill_content`'s
write-role parameter renamed `background`->`fill_color`;
`_background_candidates`'s detection-role source switched from
`infer_palette`, union, to `infer_colors_common_to_every_input`,
intersection). Raw output: `Probe checkpoint 2026-09-23: 5/200 solved
(gabarito-verified), accuracy=0.0250, unanimous=5`, `num_unanimous ==
num_solved == 5` in both, no disagreement-driven false positive.

Diff against the known v6 solved set (`23b5c85d`, `67a3c6ac`, `6fa7a44f`,
`cce03e0d`): exactly 1 new task, **`c8f0f002`**, 0 lost. Antifraud check
(knowledge item 7) passed: no decorative `selected==not_selected` branch
(the 2 verified candidates use `draw_lines`/`keep` on the selected side
against `fill(fill_color=5)` on the non-selected side, distinct roles),
no size coincidence (3 train pairs with 3 different input shapes -
(3,4), (3,6), (3,5) - each output the same shape as its own input via
`identity_canvas`), no pair-ignoring (both verified candidates match all
3 train pairs). Full detail: `docs/curriculum/rounds/round-1.md`, section
E.1.

## Probe checkpoint v8 (Round 6, `objeto_contorno` concept package, ADR 0081, 2026-09-23)

Real `cli probe` execution after the first concept round: new operation
`RecolorObjectPart`, predicate `HasInterior`, four content pieces and two
selectors in the object pack. Raw output: `Probe checkpoint 2026-09-23:
7/200 solved (gabarito-verified), accuracy=0.0350, unanimous=6`.

Diff against the v7 solved set: exactly 2 new tasks, **`50cb2852`** and
**`bb43febb`**, 0 lost. Both are solved by the top-ranked composition
`identity_canvas + all_objects + recolor_interior_selected(color) /
keep`. Antifraud check (knowledge item 7) passed: the selected and
not-selected roles differ (recolor interior vs keep), no size coincidence
(same-shape output on every pair through `identity_canvas`; 3 pairs with 3
different shapes for `50cb2852`, 2 pairs of 10x10 for `bb43febb` where
the rule does not depend on shape), and no ignored train pair (both
tasks' verified candidates match every train pair by construction).

This is the first probe-pool rise since v7 and the first from a concept
package: `unlock_value.py` listed direct unlock 0 for `objeto_contorno`, so
the tasks it solved were not those the table attributed to it. The
noop-dedup in the content prefilter also turned `c8f0f002` unanimous (20 ->
18 verified candidates); it is still solved. Full detail:
`docs/curriculum/rounds/round-6.md`.

## Probe checkpoint v9 (Round 7, `topologia_dentro` concept package, ADR 0082, 2026-09-23)

Probe pool (200 tasks, `round_sample(5)`): **7 -> 9** solved (solved@1 = 9,
solved@2 = 0; unanimous 6 -> 8). New: `810b9b61` (`objects_with_hole` +
`recolor_border_selected`) and `b2862040` (`objects_with_hole` +
`recolor_selected`), both unanimous, antifraud passed. `50cb2852` became
non-unanimous (14 candidates) but is still solved at attempt 1. Gate (779
tasks): solved=5 (@1=5, @2=0), with `00d62c1b` (fill enclosed holes) new and
accepted. Scale test: 0 of 5. Mean time per task 16.96s (max 327.8s) on the
probe. Full detail: `docs/curriculum/rounds/round-7.md`.

## Probe checkpoint v10 (Round 8, `objeto_halo` concept package, ADR 0084, 2026-09-23)

Probe pool (200 tasks, `round_sample(5)`): **9 -> 10** solved (solved@1 = 10,
solved@2 = 0; unanimous 8 -> 8). New: `4258a5f9` (`halo8_selected`, 48
candidates), antifraud passed. Gate (775 tasks): solved=3 (@1=3, @2=0),
with `dc1df850` and `f0df5ff0` new and accepted (curriculum 27); `b1948b0a`
latent, kept out. Scale test: 0 of 5. Mean time per task 21.78s (max 442.69s)
on the probe. Full detail: `docs/curriculum/rounds/round-8.md`.

## Probe checkpoint v11 (Round 9, composite object contents, ADR 0086, 2026-09-23)

Probe pool (200 tasks, `round_sample(5)`): **10 -> 12** solved (solved@1 = 12,
solved@2 = 0; unanimous 8 -> 9). New: `543a7ed5` (`fill_holes_halo8_selected`)
and `d5d6de2d` (`fill_holes_erase_selected`), both probe-only measurement.
Gate (773 tasks): solved=1 (`b1948b0a`, latent, kept out); no new acceptances
(curriculum 27). Scale test: 0 of 5. Mean time per task 25.10s (max 545.6s) on
the probe; A/B mean 40.24s, max 1496.4s; gate wall 4659.6s (Round 8: 2506s).
Composite pieces multiply object-search enumeration by 1.8-2.4x on the slowest
tasks (ADR 0089). Full detail: `docs/curriculum/rounds/round-9.md`.

## Probe checkpoint v12 (Round 10, object-search cost optimization, ADR 0090, 2026-09-24)

Probe pool (200 tasks, `round_sample(5)`): **12 -> 12** solved (solved@1 = 12,
solved@2 = 0; unanimous 9 -> 9). No new solves: this round removed repeated
work only (single enumeration per task, memoized region predicates, shared
prefilter results) and every per-task field is identical to the control.
Gate (773 tasks): solved=1 (`b1948b0a`, latent, kept out); curriculum stays 27.
Scale test: 0 of 5. Mean time per task 24.49s -> 6.47s, median 5.48s -> 2.19s,
max 990.2s -> 191.7s (`9edfc990`) on the 200-task sample at 6 workers; gate
wall 4659.6s -> 900.5s. Full detail: `docs/curriculum/rounds/round-10.md`.

## Probe checkpoint v13 (Round 11, settled slide, ADR 0091, 2026-09-24)

Probe pool (200 tasks, `round_sample(5)`): **12 -> 13** solved (solved@1 = 13,
solved@2 = 0; unanimous 9 -> 10). New: `1e0a9b12` (gravity with stacking),
accepted; curriculum 27 -> 28. Gate (773 tasks): solved=1 (`b1948b0a`, latent,
kept out). Scale test not run (next in Round 13). Mean time per task on the
probe 5.92s -> 5.79s, max 111.2s -> 104.5s. Full detail:
`docs/curriculum/rounds/round-11.md`.

## Probe checkpoint v14 (Round 12, rearrangement-aware connectivity prune, ADR 0092, 2026-09-24)

Probe pool (200 tasks): **13 -> 14** solved (solved@1 = 13, solved@2 = 1;
unanimous 10 -> 10). New: `5ffb2104`, solved on the second attempt (first @2 in
the project; the tie-break between single_color True/False candidates is
alphabetical). Gate (773 tasks): solved=2 (`d282b262` new and accepted,
`b1948b0a` latent, kept out); curriculum 28 -> 30. Scale test not run (next in
Round 13). Probe mean time per task 5.79s -> 5.69s, max 104.5s -> 100.6s. Full
detail: `docs/curriculum/rounds/round-12.md`.

## Round 13 (2026-09-24) - overlay of equal sub-grids by mask table (ADR 0094)

Probe pool 14 -> 18 of 200 (solved@1 13 -> 17, solved@2 1 -> 1). New: `281123b4`,
`e133d23d`, `e345f17b`, `f2829549`, all inherited from ARC-AGI-1 by task id; the
ARC-AGI-2-exclusive probe subset stays at 0/35. Gate (772 tasks): solved=25
(24 new accepted, `b1948b0a` latent, kept out); curriculum 30 -> 54. Scale test
0/5, max 63.9s. Probe mean 5.39s, median 2.12s, max 96.4s (`5b37cb25`). Full
detail: `docs/curriculum/rounds/round-13.md`.

## Round 15 (2026-09-24) - two-rule sequences (ADR 0097)

Probe pool 18 -> 19 of 200 (solved@1 17 -> 18, solved@2 1 -> 1); ARC-AGI-2-exclusive
probe subset stays 0/35. Gate (748 tasks): solved=7 (six sequence solves, all inherited
from ARC-AGI-1, plus latent `b1948b0a`). Cost anomaly (max 4420s, `319f2597`) traced to
the second stage; see ADR 0101. Full detail: `docs/curriculum/rounds/round-15.md`.

## Round 16 (2026-09-24) - relational extremum selection (ADR 0098)

Probe pool 19 -> 19 of 200 (solved@1 18 -> 18, solved@2 1 -> 1); arc2_only probe subset
0/35 (0/32 without the three seen tasks). Gate (748 tasks): solved=10 (9 new accepted,
`b1948b0a` latent, kept out); curriculum 54 -> 63 (2 arc2_only, the mechanism's own
acceptance tasks). Scale test 0/5, max 305.8s. Probe mean 18.32s, median 4.67s, max 259.4s
(`ad173014`); gate mean 23.26s, median 5.74s, max 817.0s (`319f2597`); sequence budget cuts
(`budget_hit`/`deadline_hit`): probe 3/0, gate 25/2, scale 3/0. Full detail:
`docs/curriculum/rounds/round-16.md`.

## Round 18 (2026-09-25) - panel grid pack, hand-solved cycle v2 (ADR 0106)

Four `arc2_only` training tasks solved by hand (`981add89`, `7acdf6d3`, `458e3a53`,
`5a719d11`); only `458e3a53` and `5a719d11` share a mechanism (grid cut by separator lines
with per-panel properties), implemented as `PanelSummary`/`PanelSwap` plus
`library/panels/`. Probe 19/200 unchanged, `arc2_only` 0/35 (0/32 without seen tasks).
Public-split proxy (120 tasks, 6 processes): 1/120 -> 1/120 (`1818057f`), 1763.5 s, max
659.5 s. Curriculum 63 -> 65 (both acceptance tasks, contaminated; `arc2_only` pool 4/198).
Hypotheses before -> after pruning: 4959 -> 847 over 1000 training tasks. Probe mean
18.12s, median 4.38s, max 252.2s; 835 tests green. Full detail:
`docs/curriculum/rounds/round-18.md`.

## Round 19 (2026-09-25, library v6): derived-parameter layer

A single registry of region properties, independent derivation operators (extremum with
ties selecting all, total, unique value, learned table) and one generic enumerator
(regions x selection x action x parameter source) replaced the dedicated relational family.
The four acceptance tasks (`5ad8a7c0`, `d6e50e54`, `ad38a9d0`, `342dd610`) are solved by
combinations of the generic layer. Probe 19/200 -> 20/200 (`arc2_only` 0/35 -> 1/35, the
seen task `342dd610`; 0/32 without seen tasks); public-split proxy 1/120 -> 1/120
(`1818057f`). Hypotheses before -> after inventory pruning: 13.1M -> 66k over 1000 training
tasks. Success criterion (a non-contaminated task solved by a combination nobody
implemented) was not met. Probe wall time rose 652.5 s -> 1091.6 s and proxy 1763.5 s ->
2338.2 s; the layer itself costs ~0.5 s per task, the cause of the rest is not isolated.
852 tests green. Full detail: `docs/curriculum/rounds/round-19.md`.

## Round 20 (coverage by volume, ADR 0108)

12 arc2_only training tasks solved by hand; added only the missing properties
(`corner_nw_color`, `closed`, `multi_cell`), a `CornerCell` region and one derived piece.
Acceptance task `17b866bd` is now solved by the solver; the other 11 are not covered (each
needs a whole mechanism; stamp/copy has 4 cases and is the Round 21 candidate). Probe
arc2_only 1/35 -> 1/35 (seen `342dd610`; 0/30 without seen); public-split proxy 1/120 ->
1/120. Hypotheses: 13.1M -> 16.3M unpruned, 66k -> 72k pruned. Full detail:
`docs/curriculum/rounds/round-20.md`.

## Round 21 (stamp, ADR 0109)

No new hand-solved tasks. Implemented the stamp mechanism (copy a region onto anchors with a
derived offset; key-cell or bbox-origin alignment, pairing by key colour or all-with-all, prior
erase none/templates/all) plus `key_color`/`key_row`/`key_col` measures. Covers 2 of the 4
named cases (`1b59e163`, `e734a0e8`, both already seen) and 4 inherited ARC-1 tasks; `83eb0a57`
and `b74ca5d1` need different mechanisms. Probe 20/200 -> 21/200 (arc2_only 2/35 with seen,
0/30 without seen), proxy 1/120 unchanged, no unseen arc2_only task solved, so no submission.
Pruned hypotheses 72,458 -> 72,548. Full detail: `docs/curriculum/rounds/round-21.md`.
