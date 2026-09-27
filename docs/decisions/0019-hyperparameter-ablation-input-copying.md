# 0019 - Hyperparameter ablation on input-copying behavior

Status: Informative

## Context

ADR 0018 found that, on a 2-task smoke sample, parsing failure is
resolved but `exact_match` is still "no" on all 7 pairs, and the model
copies the input through unchanged for `135a2760` instead of applying
the task's transformation. Before considering bigger, more expensive
levers (synthetic data augmentation, ensembling), this ablation tests a
cheaper hypothesis split at the `smoke` layer (same 2 tasks as ADR
0018, for direct comparability):

- **Under-training**: the current TTT epochs/LoRA rank are insufficient,
  and more of either would let the model escape copying the input.
- **Insufficient per-task signal**: 2-3 demonstration pairs per task
  are never enough regardless of training config, which would call for
  data augmentation instead.

Per Golden Rule 7, this stays mechanical/diagnostic (`smoke` layer, 2
tasks), no policy or lever decision is made here.

## Method

New tooling, reusing existing diagnostic infrastructure
(`generate_with_counts`, `task_selector.parse_task_selector`):

- `src/evaluation/ablation_configs.py`: three named `NeuralSolverConfig`
  variants built with `dataclasses.replace` from the same baseline,
  each isolating one axis:
  - `baseline`: current defaults (`ttt_num_epochs=3`, `lora_rank=16`,
    `lora_alpha=16`).
  - `epochs_x2`: `ttt_num_epochs=6`, rank/alpha unchanged.
  - `lora_rank_x2`: `lora_rank=32`, `lora_alpha=32`, epochs unchanged.
- `src/evaluation/run_ablation_hyperparams.py`: loads the base model
  once, then for each config x task combination attaches a fresh LoRA
  adapter, runs TTT, and diagnoses every train/test pair, adding a new
  `num_copies_of_input` field (count of kept predictions identical to
  the pair's own input grid) to the diagnostic row, specifically to
  detect the copy-paste pattern directly instead of inferring it from
  raw text alone.

Command:

```
python -m src.evaluation.run_ablation_hyperparams evaluation 136b0064,135a2760
```

Both new modules follow the existing pure/GPU-dependent split
(`ablation_configs.py` has no `unsloth` import and is host-tested,
`run_ablation_hyperparams.py` is GPU-only). Full test suite after
adding both: 66 passed (up from 62), no regressions.

## Result

### Full comparison table (3 configs x 2 tasks x 7 pairs)

| Config | Task | Split | Pair | Attempts | Parsed | Kept | Copies of input | Exact match |
|---|---|---|---|---|---|---|---|---|
| baseline | 136b0064 | train | 0 | 4 | 2 | 2 | 0 | no |
| baseline | 136b0064 | train | 1 | 2 | 2 | 2 | 0 | no |
| baseline | 136b0064 | train | 2 | 2 | 2 | 2 | 0 | no |
| baseline | 136b0064 | test | 0 | 2 | 2 | 2 | 0 | no |
| baseline | 135a2760 | train | 0 | 3 | 2 | 2 | 1 | no |
| baseline | 135a2760 | train | 1 | 2 | 2 | 2 | 0 | no |
| baseline | 135a2760 | test | 0 | 3 | 2 | 2 | 0 | no |
| epochs_x2 | 136b0064 | train | 0 | 2 | 2 | 2 | 0 | no |
| epochs_x2 | 136b0064 | train | 1 | 2 | 2 | 2 | 0 | no |
| epochs_x2 | 136b0064 | train | 2 | 3 | 2 | 2 | 0 | no |
| epochs_x2 | 136b0064 | test | 0 | 2 | 2 | 2 | 0 | no |
| epochs_x2 | 135a2760 | train | 0 | 2 | 2 | 2 | 0 | **yes** |
| epochs_x2 | 135a2760 | train | 1 | 2 | 2 | 2 | 0 | no |
| epochs_x2 | 135a2760 | test | 0 | 2 | 2 | 2 | 0 | no |
| lora_rank_x2 | 136b0064 | train | 0 | 2 | 2 | 2 | 0 | no |
| lora_rank_x2 | 136b0064 | train | 1 | 2 | 2 | 2 | 0 | no |
| lora_rank_x2 | 136b0064 | train | 2 | 2 | 2 | 2 | 0 | no |
| lora_rank_x2 | 136b0064 | test | 0 | 2 | 2 | 2 | 0 | no |
| lora_rank_x2 | 135a2760 | train | 0 | 2 | 2 | 2 | 1 | no |
| lora_rank_x2 | 135a2760 | train | 1 | 2 | 2 | 2 | 0 | no |
| lora_rank_x2 | 135a2760 | test | 0 | 2 | 2 | 2 | 0 | no |

`136b0064` shows no copy-paste behavior in any config (`num_copies_of_input`
is 0 everywhere), matching ADR 0018. The minor `attempts_tried=4` on
`baseline`/`136b0064`/train-0 (vs. 2 in ADR 0018) is expected sampling
variance from a fresh re-run, not a regression. All the ablation signal
is on `135a2760`.

### Raw text, `135a2760` train pair 0 (the pair with copy-paste in ADR 0018)

Input:

```
3333333333333
3222222222223
3213131333123
3222222222223
3333333333333
```

Expected output's third row: `3213131313123` (differs from input's
third row only in the middle digits).

**baseline** (3 attempts, 2 parsed, 2 kept, 1 copy):
- attempt 0 (kept): rows 2/4 changed to `3232222223223`, row 3 still
  `3213131333123` (unchanged from input, wrong).
- attempt 1: identical to the input, plus the model echoes back its
  own `Input:`/`Output:` prompt labels, fails to parse.
- attempt 2 (kept): identical to the input on all 5 rows, this is the
  counted copy.

**epochs_x2** (2 attempts, 2 parsed, 2 kept, 0 copies):
- attempt 0 (kept): rows 2/4 changed to `3232323123123`, row 3 still
  `3213131333123` (unchanged, wrong), same pattern as baseline's
  attempt 0, a variation that does not fix the actual transformation.
- attempt 1 (kept): rows 2/4 unchanged from input, **row 3 is
  `3213131313123`, matching the expected output exactly.** This is the
  only exact match recorded across the entire diagnostic chain since
  ADR 0009.

**lora_rank_x2** (2 attempts, 2 parsed, 2 kept, 1 copy):
- attempt 0 (kept): rows 2/4 changed to `3232222222223` (a smaller,
  partial edit than either baseline or epochs_x2's non-copy attempt),
  row 3 still `3213131333123` (unchanged, wrong).
- attempt 1 (kept): identical to the input on all 5 rows, this is the
  counted copy.

All three configs produce one "variation" attempt that edits rows 2/4
but fails to fix row 3, and two of the three configs (`baseline`,
`lora_rank_x2`) also produce one attempt that is a literal, unmodified
copy of the input. Only `epochs_x2` avoids a literal copy entirely for
this pair, and its second attempt happens to land the correct row 3.

### Raw text, `135a2760` test pair 0 (held-out, larger grid)

`num_copies_of_input` is 0 for all three configs on this pair, none of
the three configs's outputs are a literal copy of the (much larger,
29-column) test input, matching the train-pair-1 pattern where copying
also does not occur in any config. `exact_match` is "no" for all three.
Qualitatively, `baseline` and `lora_rank_x2` produce a 17-row output
close to the input's own 17-row height, while `epochs_x2` produces a
23-row output that extends the repeating band pattern further down,
diverging from the input in structure rather than reproducing it.
Since the exact ground truth transformation is not being checked here
in this note, this is one more data point that all three configs
attempt something other than a literal copy on this pair, it is not
evidence any of the three gets the transformation right on held-out
input.

### Timing per configuration

Wall-clock time was not printed by `run_ablation_hyperparams.py` in
this run, but it can be reconstructed without a re-run from two sources
already on disk: the per-task `train_runtime` figures the HF `Trainer`
already logs, and the filesystem timestamps of the raw completion files
under `outputs/raw_generations/ablation/evaluation/` (one file per
sampling attempt, written immediately after each attempt).

TTT-only time (`train_runtime`, sum over both tasks per config):

| Config | 136b0064 | 135a2760 | Sum |
|---|---|---|---|
| baseline | 49.49s | 25.49s | 74.98s |
| epochs_x2 | 45.05s | 50.1s | 95.15s |
| lora_rank_x2 | 32.33s | 24.84s | 57.17s |

Total wall time per config (TTT + all generation attempts, both tasks
combined), from the timestamp of the last raw file written in one
config to the last raw file of the next:

| Config | Total wall time (2 tasks) | Total sampling attempts | Implied s/attempt |
|---|---|---|---|
| epochs_x2 | 244.8s (4m05s) | 15 | ~9.98s |
| lora_rank_x2 | 184.2s (3m04s) | 14 | ~9.07s |
| baseline | not directly measurable (see below) | 18 | ~9.4s (estimated) |

`baseline` ran first, right after the base model finished loading, so
its raw-file timestamps are inflated by one-time model load time (4-bit
`allenai/OLMo-2-1124-7B` load, no separate log marker for its
duration). Subtracting `baseline`'s own TTT time (74.98s) and an
estimated generation cost (18 attempts x ~9.4s/attempt, using the
per-attempt rate implied by the other two configs, which agree with
each other to within 10%) from its inclusive wall time (494.6s, from
process start to its last raw file) gives an estimated model load time
of ~249s (~4.1 min) and an estimated `baseline` task-only wall time of
~246s, close to `epochs_x2`'s directly measured 244.8s despite having
half the epochs, because `baseline` needed more sampling attempts (18
vs. 15) to reach the same `num_kept=2` on every pair, eating into the
time saved by fewer epochs.

This estimate is a derived reconstruction, not a value the script
explicitly measured, and is presented with that caveat. The instrumented
per-attempt generation cost stays roughly constant (~9-10s) across all
three configs, consistent with generation cost being driven by
`max_new_tokens`/grid size, not by LoRA rank or epoch count.

**Takeaway for the time budget:** doubling TTT epochs (`epochs_x2`)
increases per-task wall time (~245s for 2 tasks vs. `lora_rank_x2`'s
~184s), and would scale directly with epoch count on top of an already
tight per-task time budget (see ADR 0013). Doubling LoRA rank
(`lora_rank_x2`) had negligible wall-time cost in this sample, but also
showed no accuracy signal.

## Decision

No lever is decided here, per the user's explicit request and Golden
Rule 7. The finding, on this two-task, one-pair sample:

- **Copy-paste is not universal across configs on the same pair.**
  `baseline` and `lora_rank_x2` both still produce a literal, unmodified
  copy of the input as one of their two kept predictions for
  `135a2760` train pair 0. `epochs_x2` does not, for this same pair,
  and instead produces the only exact match seen in the whole
  diagnostic chain (ADR 0009 through 0019).
- **This is weak, narrow evidence, not a resolved question.** The
  exact match is on a *train* pair, the same pair TTT trains on
  directly, so it is closer to evidence that more epochs help the
  model fit its own training data (reducing under-fitting/copy-paste on
  a seen example) than evidence of generalization to unseen input. The
  held-out test pair for the same task shows `exact_match: no` for all
  three configs, including `epochs_x2`.
- **Doubling LoRA rank shows no comparable effect** on this sample,
  `lora_rank_x2` behaves like `baseline` on the one pair that showed
  copy-paste (one copy, one wrong variation), not like `epochs_x2`.
- This is a single pair on a single task. Per Golden Rule 7, it cannot
  by itself justify picking a hyperparameter-tuning lever over data
  augmentation, it is a signal that more epochs is the more promising
  of the two hyperparameter axes tested here, worth a larger sample
  before committing resources either way.

## Consequences

- No solver defaults changed. `NeuralSolverConfig` still defaults to
  `ttt_num_epochs=3`, `lora_rank=16`, `lora_alpha=16`.
- New diagnostic tooling (`ablation_configs.py`,
  `run_ablation_hyperparams.py`, `num_copies_of_input` field) stays
  available for a future, larger-sample re-run.
- CLAUDE.md Section 6 "Missing" item is updated to reflect this
  narrower finding: doubling epochs looks more promising than doubling
  LoRA rank on this one pair, but the evidence is a single train-pair
  exact match, not a resolved hypothesis, and the next step (broaden
  the epochs axis to a `sanity`/`validation` sample, or move to data
  augmentation) is still an open joint decision.

## Alternatives considered

- **Run this ablation at the `sanity` layer (8 tasks) instead of
  `smoke` (2 tasks):** rejected for now, this is a cheap mechanical
  check meant to rule hyperparameters in or out before committing to a
  larger, more expensive run; Golden Rule 7 reserves the larger sample
  for the actual policy decision, not this preliminary screen.
- **Treat the `epochs_x2` train-pair exact match as sufficient to pick
  "more epochs" as the lever now:** rejected, explicitly per the user's
  instruction to decide jointly, and because the match is on a training
  pair, not held-out input, so it does not yet demonstrate the model
  learned the transformation rather than fit that one example harder.
- **Test epochs and rank jointly (e.g. `epochs_x2` + `lora_rank_x2`
  combined) in this same pass:** rejected for this round, isolating one
  axis per config keeps attribution clean; a combined config is a
  reasonable follow-up if a larger epochs-only sample looks promising.

## References

- [ADR 0009 - Empty-candidate diagnosis](0009-empty-candidate-diagnosis.md)
- [ADR 0010 - Raw generation inspection](0010-raw-generation-inspection.md)
- [ADR 0015 - Layered sampling](0015-layered-sampling.md)
- [ADR 0017 - Post-EOS-fix sanity diagnosis](0017-post-eos-fix-sanity-diagnosis.md)
- [ADR 0018 - Post-EOS-fix parsing-vs-content diagnosis](0018-post-eos-fix-parsing-vs-content-diagnosis.md)
