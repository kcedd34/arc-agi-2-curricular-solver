# 0026 - Shape constraint at the sanity layer

## Status

Informative. Promotes ADR 0025's evidence tier from `smoke` (2 tasks) to
`sanity` (8 tasks, same sample as ADR 0017/0023/0024), per Golden Rule 7.
Does not itself license adopting the constraint as a permanent default;
see Consequences for the `validation`-layer bar that still applies.

## Context

ADR 0025 (smoke-tier, 2 tasks) showed the truncate/pad shape constraint
fixes both sampled held-out test pairs' shape without changing
`exact_match`. This run extends to the 8-task/11-test-pair sample ADR
0017/0023/0024 already used, and answers four questions: does shape now
match expected, does `exact_match` move, how close is content once
shape is corrected, and does self-consistency behave differently.

## Method

`src/evaluation/run_shape_constraint_sanity.py`, using
`sample_tiers.select_tier_tasks(tasks, "sanity")` (first 8 tasks by id)
instead of ADR 0025's hardcoded 2-task list; same single-generation-pass
measurement as ADR 0025 (`shape_constraint_diagnostics.py`). Added one
new field, `constrained_best_cell_accuracy`
(`pair_diagnostics.per_cell_accuracy`, max across kept constrained
predictions), to read content proximity once shape stops confounding
the comparison. Also added a diagnostic-only self-consistency read: per
task, whether every train pair reaches `exact_match`, unconstrained vs.
constrained (does not call the real `_passes_self_consistency` gate,
reuses the rows already captured for the other three questions).

## Results

### 1. Does shape now match expected, with the constraint applied?

11 held-out test pairs, same sample as ADR 0017/0023/0024:

| Group | Test pairs | Constrained shape match |
|---|---|---|
| Rule does not hold (`0934a4d8`, `136b0064`) | 2 | no (unchanged, correctly left unconstrained) |
| Rule holds, something parsed | 8 | yes, 8/8 |
| Rule holds, nothing parsed (`13e47133` test 1, 0/6 attempts kept) | 1 | n/a, nothing to constrain |

Confirms ADR 0025's finding at 4x the sample: every held-out test pair
where the rule holds and at least one candidate parses gets its shape
corrected (8/8, up from ADR 0025's 2/2). The one exception is not a
constraint failure, it is a total parsing failure upstream of the
constraint (0 kept predictions across all 6 attempts). The constraint
operates on parsed grids and cannot rescue a pair where nothing parses
at all. The same task (`13e47133`) also fails to parse anything on one
of its three train pairs, and shows a total wall time of 1521s vs.
61-441s for the other 7 tasks, extending ADR 0023's unexplained
generation-timing anomaly on this exact task with a concrete correlate
(repeated failed attempts), still not investigated further.

### 2. Does `exact_match` change with shape corrected?

No. 0/32 rows (21 train + 11 test) reach `exact_match`, constrained or
not. Confirms ADR 0025's smoke-tier reading at sanity scale: shape
correction unblocks the possibility, content remains wrong everywhere
in this sample.

### 3. Content proximity once shape stops confounding the read

`constrained_best_cell_accuracy`, only computable where the constrained
prediction's shape matches (comparable cell-by-cell), across the 8
held-out test pairs where the rule holds and something parsed:

| Task | Test pair | Cell accuracy |
|---|---|---|
| `13e47133` | 0 | 0.19 |
| `142ca369` | 0 | 0.45 |
| `16de56c4` | 0 | 0.59 |
| `16de56c4` | 1 | 0.73 |
| `135a2760` | 0 | 0.77 |
| `142ca369` | 1 | 0.81 |
| `16b78196` | 0 | 0.90 |
| `1818057f` | 0 | 0.90 |

Mean 0.67, but the spread is the real signal, not the mean: 5 of 8
pairs are "close" (0.73-0.90, most cells right), 2 are "middling" (0.45,
0.59), and 1 is clearly "far" (`13e47133`, 0.19, close to what a
structurally wrong guess would produce). `13e47133` is also the task
with the two outright parse failures and the timing anomaly noted
above, three separate signals now converging on the same task as
qualitatively different from the rest of the sample, not just
quantitatively worse.

Training pairs (in-distribution, TTT trained on them directly) confirm
the same pattern at a higher baseline: 0.75-0.99 for every task except
`13e47133` (0.37, 0.45), which stays low even on pairs the model
trained on directly. This rules out "held-out generalization gap" as
the explanation for `13e47133` specifically, since it cannot even fit
its own training pairs well within 3 epochs, unlike the other 5
rule-holding tasks.

### 4. Self-consistency behavior

Unchanged: the all-train-pairs-`exact_match` read stays "no" for all 8
tasks, constrained and unconstrained alike. Shape was never what caused
self-consistency to reject these tasks: `exact_match` requires literal
content equality, and content is wrong on every train pair regardless
of whether its shape happens to be right (several rule-holding tasks
already had correct unconstrained shape on some train pairs, e.g.
`16de56c4`, `1818057f`, `135a2760`, yet still failed `exact_match`
there). Correcting shape does not, and was not expected to, move this
gate; it was already gated on content, not shape.

## Consequences

- Promotes ADR 0025's constraint from smoke-tier to sanity-tier
  evidence: the shape fix generalizes cleanly (8/8 fixable pairs fixed)
  across the same 8-task sample used throughout this diagnostic chain,
  with one known, orthogonal boundary condition (it cannot fix a pair
  where nothing parses at all).
- Per Golden Rule 7, sanity-tier evidence still does not license a
  policy/architecture ADR on its own; a `validation`-layer run (30-50
  tasks) remains the bar before treating this as a permanent default.
  This ADR's Status stays Informative for that reason, even though the
  result is uniformly positive within its sample.
- `exact_match` is confirmed unaffected, so it can now be read as a
  purer content-correctness signal for the two content-lever candidates
  from ADR 0022, no longer confounded by the row-count shape gap ADR
  0024 diagnosed.
- `13e47133` stands out across three independent signals (lowest cell
  accuracy, only task with total parse failures, only task with the
  wall-time anomaly) and looks like a materially different failure mode
  from the rest of the rule-holding sample; worth tracking as its own
  item rather than averaging it into a single "content is X% right"
  number for the whole sample.

## Initial recommendation on the ADR 0022 content lever (not a decision)

With shape no longer confounding the read, the per-cell accuracy spread
suggests the content gap is not uniform across tasks, which weakly
favors different fixes for different failure shapes rather than one
lever for everything:

- 5 of 8 rule-holding test pairs are "close" (0.73-0.90 cell accuracy)
  and even closer on their own training pairs (up to 0.99) without ever
  reaching exact match. This looks like the model has largely learned
  each task's transformation but applies it with residual, seemingly
  non-systematic per-cell noise, consistent with under-constrained or
  under-augmented fitting rather than a missing capability. **Color
  augmentation** (ADR 0022's first candidate) targets exactly this: more
  varied views of the same transformation to tighten the fit.
- `13e47133` (0.19-0.45, including on its own training pairs, plus
  outright parse failures) looks structurally different: not a
  near-miss, closer to not having grasped the task at all. This is the
  profile ADR 0022's cross-task pretraining hypothesis was framed
  around: a capability gap that augmenting that one task's own few
  pairs would not be expected to fix.

My initial lean, to discuss jointly: try color augmentation first, since
it is the smaller, cheaper change and this sample suggests it stands to
convert several "close" tasks toward exact match, while treating
`13e47133`-like tasks as a named open question rather than assuming
augmentation should fix them too. If a `validation`-layer run later
shows `13e47133`'s profile (low cell accuracy plus parse failures) is
common rather than a single outlier, that would be the trigger to
prioritize cross-task pretraining instead. This is not a decision, per
the standing instruction to keep ADR 0022 open until this data existed.

## Alternatives considered

- Reusing ADR 0025's smoke-tier task pair (`135a2760`, `1818057f`)
  instead of the ADR 0017/0023/0024 8-task sample: rejected, the point
  of the sanity extension is comparability with the existing diagnostic
  chain's exact sample, not a differently composed set of 8 tasks.
- Calling the real `neural_solver._passes_self_consistency` for the
  self-consistency read: rejected, it re-runs generation (a second GPU
  pass per pair) for a question already answerable from rows already
  captured; the diagnostic read documented above is explicitly not the
  production gate, just a reuse of already-captured `exact_match` rows.
