# 0021 - Geometric augmentation smoke test

Status: Informative

## Context

ADR 0020 picked synthetic data augmentation as the next content-side
lever, deferring design to a joint planning pass. Before that pass, the
user asked for a first mechanical check: implement geometric-only
(D4 dihedral group) augmentation of the demonstration pairs used in
TTT, and smoke-test it on the same 2 tasks ADR 0018/0019 used
(`136b0064`, `135a2760`), specifically checking whether the "copies the
input" pattern disappears on the **held-out test pair**, and measuring
the TTT time cost of up to 8x more training examples per task. No color
augmentation, no production variant count decided here, per the user's
explicit instruction.

**Discovery made before any new code was written:** geometric
augmentation of exactly this shape already existed in the codebase
(`src/utils/grid_ops.py`'s `GEOMETRIC_TRANSFORMS`, wired unconditionally
into `train_on_task` via `src/solvers/neural/prompt_builder.py`). Every
prior diagnostic run in this chain (ADR 0009 through ADR 0019/0020) had
already trained on this augmented set, not raw pairs. There was no way
to produce a genuine "no augmentation" baseline as the request assumed
existed. Two concrete gaps closed this against the literal spec:

- `GEOMETRIC_TRANSFORMS` had only 7 of the 8 dihedral elements, missing
  the anti-diagonal reflection.
- No config flag existed to disable augmentation for a true control
  group.

## Method

- `src/utils/grid_ops.py`: added `anti_transpose` (reflection across
  the anti-diagonal, `rotate180(transpose(grid))`), completing
  `GEOMETRIC_TRANSFORMS` to all 8 D4 elements. Also used by
  `error_classifier.py` and `baseline_solver.py` for the symbolic
  baseline's exhaustive geometric search, both widen their search space
  as a side effect, not a regression.
- `src/solvers/neural/config.py`: new `use_geometric_augmentation: bool
  = True` field on `NeuralSolverConfig`, default preserves existing
  behavior for the rest of the pipeline.
- `src/solvers/neural/prompt_builder.py`: `build_training_examples` now
  takes `transforms` as a parameter (default `GEOMETRIC_TRANSFORMS`),
  enabling a genuine no-augmentation path via `[identity]`. The same
  transform is applied to both input and output of every demonstration
  pair, never to the test pair, matching the request exactly.
- `src/solvers/neural/ttt_trainer.py`: `train_on_task` picks
  `GEOMETRIC_TRANSFORMS` or `[identity]` based on
  `config.use_geometric_augmentation`.
- `src/evaluation/augmentation_configs.py`: two named configs,
  `no_augmentation` (`use_geometric_augmentation=False`) and
  `geometric_full` (`use_geometric_augmentation=True`, the default),
  same `dataclasses.replace` pattern as `ablation_configs.py`.
- `src/evaluation/diagnostic_runner.py`: shared per-task/per-pair
  diagnostic plumbing, extracted from `run_ablation_hyperparams.py` so
  the new smoke script does not duplicate it. Adds direct timing
  capture via `time.monotonic()` around `train_on_task` (`ttt_seconds`)
  and around the full per-task diagnose call including generation
  (`total_seconds`), to avoid ADR 0019's after-the-fact timestamp
  reconstruction.
- `src/evaluation/run_augmentation_smoke.py`: same structure as
  `run_ablation_hyperparams.py`, using `build_augmentation_configs()`.

Command:

```
python -m src.evaluation.run_augmentation_smoke evaluation 136b0064,135a2760
```

Full test suite after all changes: 77 passed, no regressions.

## Result

### Full comparison table (2 configs x 2 tasks x 7 pairs)

| Config | Task | Split | Pair | Attempts | Parsed | Kept | Copies of input | Exact match |
|---|---|---|---|---|---|---|---|---|
| no_augmentation | 136b0064 | train | 0 | 6 | 0 | 0 | 0 | no |
| no_augmentation | 136b0064 | train | 1 | 6 | 0 | 0 | 0 | no |
| no_augmentation | 136b0064 | train | 2 | 6 | 1 | 1 | 0 | no |
| no_augmentation | 136b0064 | test | 0 | 6 | 0 | 0 | 0 | no |
| no_augmentation | 135a2760 | train | 0 | 4 | 2 | 2 | 0 | no |
| no_augmentation | 135a2760 | train | 1 | 6 | 2 | 2 | 0 | no |
| no_augmentation | 135a2760 | test | 0 | 6 | 1 | 1 | 0 | no |
| geometric_full | 136b0064 | train | 0 | 2 | 2 | 2 | 0 | no |
| geometric_full | 136b0064 | train | 1 | 2 | 2 | 2 | 0 | no |
| geometric_full | 136b0064 | train | 2 | 2 | 2 | 2 | 0 | no |
| geometric_full | 136b0064 | test | 0 | 2 | 2 | 2 | 0 | no |
| geometric_full | 135a2760 | train | 0 | 2 | 2 | 2 | 1 | no |
| geometric_full | 135a2760 | train | 1 | 2 | 2 | 2 | 0 | no |
| geometric_full | 135a2760 | test | 0 | 6 | 1 | 1 | 0 | no |

`exact_match` is "no" on every single pair in this table, in both
configs, **including every held-out test pair.** `num_copies_of_input`
is nearly absent in both configs (only one non-zero cell across the
whole table, `geometric_full`/`135a2760`/train/0), markedly less than
ADR 0018/0019's baseline, though `no_augmentation` here is a genuinely
new (smaller-training-set) condition never tested before, so this is
not a like-for-like comparison against ADR 0019's "baseline".

### The original question, answered directly: does the copy-input pattern persist on held-out test pairs under `geometric_full`?

**No.** Both held-out test pairs for `geometric_full` show
`num_copies_of_input: 0`, and in both cases parsing succeeded
(`136b0064` test: `num_kept=2`; `135a2760` test: `num_kept=1`), so this
is a real answer, not an artifact of nothing being parseable to check.
Direct inspection of the kept predictions against the true test input
confirms the count is not an edge case:

- `136b0064` test pair (input 19 rows, output a differently-shaped
  19x7 grid): both kept predictions (`geometric_full_136b0064_test_0_0.txt`,
  `_1.txt`) are structurally unlike the input, one an 8-row grid, the
  other a 21-row grid with different content, wrong either way but not
  a copy.
- `135a2760` test pair (input and expected output both 29 rows x 30
  columns of a repeating banded pattern): the one kept prediction
  (`geometric_full_135a2760_test_0_1.txt`) is only 18 rows, well short
  of the 29-row input/output, again wrong but structurally distinct
  from a copy.

**This answers the question the whole smoke test was built to
answer:** under `geometric_full` (8x augmentation, which per the
discovery above was already active in every prior ADR since 0009), the
model does not fall back to literally copying the held-out input. The
remaining failure mode on held-out pairs in this sample is content/
structure being wrong in some other way (wrong grid size, wrong
pattern), not input-copying. This is still a 2-task sample and does
not show the model gets the transformation *right*, only that its
wrong answers on held-out input are not literal copies.

### Parsing reliability differs sharply between configs

This is the clearest signal in this sample, and it was not the
question the smoke test set out to answer:

- `no_augmentation` fails to parse **any** valid grid at all for 2 of
  its `136b0064` pairs (train 0 and train 1, `num_parsed=0` out of 6
  attempts each). Its raw completions for these pairs are not malformed
  grids, they are runaway repetition: a single line of digits with no
  newline structure at all, repeating a short pattern for the entire
  `max_new_tokens` budget (`606011040000000` repeated ~170+ times in
  `no_augmentation_136b0064_train_0_0.txt`), never emitting the newline
  structure or a stop signal the ADR 0010 EOS fix was meant to produce.
- `geometric_full` parses successfully on essentially the first 2
  attempts for almost every pair (`attempts=2, parsed=2, kept=2` in 6
  of 7 rows), producing well-formed, correctly-shaped grids
  immediately.

This points at a plausible read consistent with ADR 0019's "insufficient
per-task signal" hypothesis: 2-3 raw demonstration pairs may be too few
for the model to reliably reproduce even the basic grid-text *format*
during TTT (not just the transformation), and 8x more examples of the
same format (even geometrically transformed) measurably stabilizes
that formatting behavior. This is a sample of 2 tasks and is not proof
of a general effect.

### Qualitative check, `geometric_full` / `135a2760` train pair 0 (the one copy)

Input:

```
3333333333333
3222222222223
3213131333123
3222222222223
3333333333333
```

- attempt 0 (kept): rows 2/4 changed to `3232222223223`, row 3 still
  `3213131333123` (unchanged from input, wrong), the same kind of
  partial-edit-that-misses-row-3 pattern ADR 0019 saw across all three
  of its configs on this exact pair.
- attempt 1 (kept): identical to the input on all 5 rows, this is the
  one counted copy.

Same qualitative shape as ADR 0019's `baseline`/`lora_rank_x2` on this
pair: one non-copy variation that edits the wrong rows, one literal
copy. Augmentation did not change this pair's behavior in this sample.

### Timing

| Config | Task | TTT seconds | Total seconds |
|---|---|---|---|
| no_augmentation | 136b0064 | 30.55 | 1830.90 |
| no_augmentation | 135a2760 | 5.29 | 1112.62 |
| geometric_full | 136b0064 | 26.29 | 67.68 |
| geometric_full | 135a2760 | 29.16 | 448.20 |

**Caveat, read before drawing any conclusion from this table:** taken
at face value this says `no_augmentation` is dramatically *slower*
overall despite training on fewer examples, and `geometric_full`
dramatically faster, which contradicts what more training examples
alone would predict and is very likely a measurement artifact, not a
real effect of the augmentation flag. `no_augmentation` ran **first**
in this process (see `build_augmentation_configs`'s config order), and
`total_seconds` covers TTT plus every pair's generation calls for that
task. A one-time GPU/CUDA warmup cost (kernel autotuning, first-call
compilation) landing entirely inside the first config/task processed in
the whole run would produce exactly this shape: `no_augmentation`'s
`ttt_seconds` (30.55s, 5.29s) are actually smaller than
`geometric_full`'s (26.29s, 29.16s is comparable, 26.29s slightly
smaller) despite 8x fewer training examples, consistent with fewer
examples training faster, while `total_seconds` is inflated by roughly
1800s and 1100s respectively, an order of magnitude larger than the
`ttt_seconds`/generation cost either config would plausibly need. This
was not isolated by a reversed-order re-run or a separately warmed GPU
state in this pass, so it is reported here as an unresolved measurement
artifact, not as evidence that augmentation is faster. **The one number
that can be read directly and is not confounded this way is
`ttt_seconds` itself: 8x more training examples cost 26.29s vs 30.55s
and 29.16s vs 5.29s, i.e. TTT time did not scale anywhere near 8x with
8x more examples in this sample,** which is itself worth noting for the
ADR 0013 time budget, though a 2-task sample is too small to trust the
magnitude.

## Decision

No lever is decided here, no color augmentation implemented, no
production variant count chosen, per the user's explicit instruction
and Golden Rule 7. Findings, on this 2-task sample:

- The specific question asked (does the copy-input pattern disappear
  on held-out test input under augmentation) has a direct answer:
  **yes, in this sample.** Both `geometric_full` held-out test pairs
  show `num_copies_of_input: 0`, with parsing succeeding on both, so
  neither is a "nothing to check" case. This does not mean the model
  gets the transformation right on held-out input (`exact_match` is
  still "no" on both), only that its wrong answers there are
  structurally distinct from the input, not literal copies.
- The most concrete new signal is that `no_augmentation` produces
  outright unparseable, runaway-repetition output for 2 of 7 pairs,
  while `geometric_full` parses reliably almost everywhere, consistent
  with "too few demonstration pairs" being at least partly a format
  problem, not only a content one.
- The timing table's `total_seconds` column carries an unresolved,
  likely first-run GPU-warmup confound and must not be read as "the
  time cost of augmentation" without that caveat. `ttt_seconds` alone
  suggests TTT time does not scale linearly with 8x more examples, but
  this is a 2-task, unverified observation.

## Consequences

- No solver defaults changed. `NeuralSolverConfig.use_geometric_augmentation`
  still defaults to `True`, matching what every prior ADR in this chain
  already ran with (now with the corrected 8-element `GEOMETRIC_TRANSFORMS`
  instead of 7).
- New tooling (`augmentation_configs.py`, `run_augmentation_smoke.py`,
  `diagnostic_runner.py` with direct timing) stays available for a
  larger-sample re-run.
- The GPU-warmup timing confound is an open item: a future timing
  comparison should either discard the first config/task's
  `total_seconds` or run a dedicated warmup pass before measuring, to
  get a trustworthy wall-clock comparison.
- Color augmentation and the final production augmentation variant
  count remain undecided, both explicitly deferred to a joint decision
  as instructed.

## Alternatives considered

- **Re-run with reversed config order to isolate the warmup confound
  before writing this ADR:** rejected for this round, this is already a
  `smoke`-layer check per Golden Rule 7 and the user asked for the
  ratio/number to be reported for a joint decision, not for the
  ambiguity to be resolved unilaterally first; flagged as an open item
  instead.
- **Treat `ttt_seconds` alone as sufficient to conclude augmentation is
  cheap:** rejected, a 2-task sample is not enough to trust the
  magnitude, only enough to report the direction and defer the
  decision, consistent with Golden Rule 7.

## References

- [ADR 0009 - Empty-candidate diagnosis](0009-empty-candidate-diagnosis.md)
- [ADR 0010 - Raw generation inspection](0010-raw-generation-inspection.md)
- [ADR 0013 - Time budget for 240 tasks](0013-time-budget-240-tasks.md)
- [ADR 0015 - Layered sampling](0015-layered-sampling.md)
- [ADR 0018 - Post-EOS-fix parsing-vs-content diagnosis](0018-post-eos-fix-parsing-vs-content-diagnosis.md)
- [ADR 0019 - Hyperparameter ablation on input-copying behavior](0019-hyperparameter-ablation-input-copying.md)
- [ADR 0020 - Next accuracy lever: data augmentation, not hyperparameter tuning](0020-lever-decision-data-augmentation.md)
