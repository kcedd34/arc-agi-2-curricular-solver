# 0009 - Empty-candidate diagnosis (neural self-consistency and symbolic fallback)

**Status:** Informative (2026-09-07)

## Context

ADR 0008 found that all 11/11 test pairs in the 8-task evaluation sample
ended up with zero candidate grids, from both the neural solver and the
symbolic baseline fallback. That ADR did not investigate *why* - this one
does, as two separate investigations, before any improvement lever is
chosen. Nothing in this ADR changes solver behavior; the neural path was
re-run once more with counting added around the existing sampling loop
(`src/evaluation/generation_diagnostics.py`, `run_generation_diagnostics.py`),
the symbolic path was checked by directly calling the existing pure
functions (no re-run needed, no GPU).

## Investigation A: neural path (self-consistency + parsing)

`src/solvers/neural_solver.py:29-34` (`_passes_self_consistency`) requires,
for every train pair, that the pair's exact expected output appear among
the up to `num_predictions` (2) grids kept by `generate_grid_predictions`
(itself sampling up to `num_predictions * 3` = 6 attempts, keeping unique
valid grids, see `src/solvers/neural/generation.py:27-38`). Any single
train pair failing this short-circuits the whole task to the baseline
fallback (`_predict_task_with_neural_solver` returns `None`).
`src/solvers/neural/grid_serialization.py:21-30` (`text_to_grid`) silently
returns `None` for any decoded text that isn't a rectangular grid of
digits 0-9, no logging of why a given attempt was rejected.

Re-ran the same 8 tasks with the sampling loop instrumented to record, per
pair (train and test), how many attempts were tried, how many decoded to a
valid grid (`num_parsed`), how many were kept after dedup
(`num_kept`), and whether the pair's exact expected output was ever
produced (`exact_match`). Raw per-task JSON persisted under
`outputs/diagnostics/generation_counts/evaluation/{task_id}.json`
(gitignored) so this run doesn't need repeating either.

| Task | Split | Pair | Attempts tried | Parsed | Kept | Exact match |
|---|---|---|---|---|---|---|
| 0934a4d8 | train | 0 | 6 | 1 | 1 | no |
| 0934a4d8 | train | 1 | 6 | 0 | 0 | no |
| 0934a4d8 | train | 2 | 6 | 0 | 0 | no |
| 0934a4d8 | train | 3 | 6 | 1 | 1 | no |
| 0934a4d8 | test | 0 | 6 | 0 | 0 | no |
| 135a2760 | train | 0 | 6 | 0 | 0 | no |
| 135a2760 | train | 1 | 6 | 0 | 0 | no |
| 135a2760 | test | 0 | 6 | 0 | 0 | no |
| 136b0064 | train | 0 | 2 | 2 | 2 | no |
| 136b0064 | train | 1 | 6 | 5 | 2 | no |
| 136b0064 | train | 2 | 6 | 6 | 2 | no |
| 136b0064 | test | 0 | 2 | 2 | 2 | no |
| 13e47133 | train | 0 | 6 | 0 | 0 | no |
| 13e47133 | train | 1 | 6 | 0 | 0 | no |
| 13e47133 | train | 2 | 6 | 0 | 0 | no |
| 13e47133 | test | 0 | 6 | 0 | 0 | no |
| 13e47133 | test | 1 | 6 | 0 | 0 | no |
| 142ca369 | train | 0 | 6 | 0 | 0 | no |
| 142ca369 | train | 1 | 6 | 0 | 0 | no |
| 142ca369 | train | 2 | 6 | 0 | 0 | no |
| 142ca369 | test | 0 | 6 | 0 | 0 | no |
| 142ca369 | test | 1 | 6 | 0 | 0 | no |
| 16b78196 | train | 0 | 6 | 0 | 0 | no |
| 16b78196 | train | 1 | 6 | 0 | 0 | no |
| 16b78196 | test | 0 | 6 | 0 | 0 | no |
| 16de56c4 | train | 0 | 6 | 0 | 0 | no |
| 16de56c4 | train | 1 | 6 | 0 | 0 | no |
| 16de56c4 | train | 2 | 2 | 2 | 2 | no |
| 16de56c4 | test | 0 | 6 | 0 | 0 | no |
| 16de56c4 | test | 1 | 6 | 0 | 0 | no |
| 1818057f | train | 0 | 6 | 0 | 0 | no |
| 1818057f | train | 1 | 6 | 0 | 0 | no |
| 1818057f | train | 2 | 6 | 0 | 0 | no |
| 1818057f | test | 0 | 6 | 0 | 0 | no |

**Reading the numbers:**

- `exact_match` is `no` on all 34 rows (train and test combined). Self-consistency never passed on a single train pair, in any task, so `_passes_self_consistency` short-circuited on the first train pair every time.
- Two distinct failure modes are visible, not one:
  - **Total parsing failure** (`num_parsed` = 0 on every single row of the task, i.e. across up to 6 sampling attempts per pair, the decoded text never once formed a valid rectangular 0-9 grid): 5 of 8 tasks (135a2760, 13e47133, 142ca369, 16b78196, 1818057f) - 27 of 34 rows (79%) overall.
  - **Parsing works, content wrong** (valid grids ARE produced, but none ever equal the expected output): 3 of 8 tasks (0934a4d8 partially, 136b0064 fully - every row hit the `num_kept` = 2 cap, some in as few as 2 attempts -, 16de56c4 partially) - 7 of 34 rows (21%).
- No task shows a "close but rejected" pattern in this sample - either generation never produces a parseable grid at all, or it produces well-formed but exactly-wrong grids. There is no case here where self-consistency discarded a prediction that was merely borderline.

This means the empty final output is **not mainly a self-consistency
threshold problem** in this sample: for 5 of 8 tasks the bottleneck is
upstream of self-consistency entirely (generation/parsing never yields a
usable grid), and for the other 3 (where parsing works cleanly, notably
136b0064 at a 100% parse rate) the model's predictions are simply wrong on
every attempt, not near-misses that a looser threshold would rescue.
Training itself converges normally in all 8 runs (final TTT loss in the
same 0.10-0.32 range as previously documented), so the training loop is
not the visible cause of either failure mode.

## Investigation B: symbolic path (baseline fallback)

`src/solvers/baseline_solver.py:28-44` (`predict_test_input`) has no
fallback beyond its two mechanisms: geometric transforms (including
identity) that must fit *all* train pairs exactly, and a strict 1-to-1
color mapping that requires identical input/output shape across all train
pairs with no conflicting cell mapping. When neither applies, it returns
`[]` for that test input - confirmed by reading the code, not inferred.
There is no default guess (no identity fallback, no nearest-transform,
no partial-credit candidate).

Checked directly (no re-run of the solver, pure function calls) for the
same 8 tasks:

| Task | Matching transforms | Color mapping | Baseline predictions per test pair |
|---|---|---|---|
| 0934a4d8 | none | shape differs (mapping impossible) | [0] |
| 135a2760 | none | conflict (no valid mapping) | [0] |
| 136b0064 | none | shape differs (mapping impossible) | [0] |
| 13e47133 | none | conflict (no valid mapping) | [0, 0] |
| 142ca369 | none | conflict (no valid mapping) | [0, 0] |
| 16b78196 | none | conflict (no valid mapping) | [0] |
| 16de56c4 | none | conflict (no valid mapping) | [0, 0] |
| 1818057f | none | conflict (no valid mapping) | [0] |

No task in this sample has a matching geometric transform (not even
identity) or a conflict-free color mapping, so the baseline correctly and
predictably returns zero candidates for every one of them. This is
expected given the baseline's documented scope (ADR 0001: "cheap
fallback/verification layer", not a general solver) - it was never
designed to cover tasks like these. Whether that scope should be widened
is a design question, not a bug.

## What this does and does not establish

- Does establish: in this 8-task sample, the empty-candidate outcome has
  two largely independent causes - the neural solver's generation step
  frequently never produces a parseable grid at all (5/8 tasks), and even
  when it does, the produced grids are exactly wrong rather than close
  (3/8 tasks); separately, the symbolic baseline's two mechanisms never
  apply to any of these 8 tasks by construction.
- Does not establish: whether loosening the self-consistency criterion
  (e.g., majority vote instead of unanimous, or accepting near-matches)
  would help, since no near-miss was observed here to loosen toward -
  this sample gives either zero valid output or exactly-wrong valid
  output. Also does not establish why parsing fails so often for 5 of the
  8 tasks (prompt format, generation length, temperature, TTT data volume,
  or something else) - the raw generated text itself was not captured in
  this diagnostic pass and would be the next thing to inspect if that
  question becomes the priority.

## Next step (not decided here)

No fix is chosen or implemented in this ADR. Candidate levers this raises
for a joint decision include: inspecting raw (unparsed) generation output
to understand the 79% parsing failure rate, relaxing or restructuring the
self-consistency criterion, and widening the symbolic baseline's scope -
but picking among them, or something else entirely, is deferred to that
discussion.

## References

- [ADR 0001 - Solver approach selection](0001-solver-approach-selection.md) (baseline scoped as a cheap fallback, not a general solver)
- [ADR 0003 - Base model and fine-tuning strategy](0003-base-model-and-finetuning-strategy.md)
- [ADR 0007 - Raw prediction persistence](0007-raw-prediction-persistence.md)
- [ADR 0008 - Error diagnosis, first round](0008-error-diagnosis-first-round.md) (the 0/11 empty-candidate finding this ADR investigates)
