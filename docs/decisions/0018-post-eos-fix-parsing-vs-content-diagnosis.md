# 0018 - Post-EOS-fix parsing-vs-content diagnosis

Status: Informative

## Context

ADR 0017 confirmed the sanity-tier run still scores 0/11 after the ADR
0010 EOS fix and the ADR 0014 model swap, but that run captured no raw
pre-parsing text, so it could not tell whether the remaining failure is
still malformed generation (parsing) or valid-but-wrong grids (content).
Per Golden Rule 7, this is mechanical debugging, not a policy decision,
so it runs at the `smoke` layer (1-2 tasks), not a full `sanity` sample.

## Method

Reused `run_generation_diagnostics.py` (built for ADR 0009/0010) against
the same two tasks ADR 0009 already has numbers for, now with
OLMo-2-1124-7B and the EOS fix applied:

- `136b0064`: the one task with 100% successful parsing before the fix.
- `135a2760`: a task with total parsing failure before the fix.

`run_generation_diagnostics.py` gained support for an explicit task-id
selector (`task_selector.py`, `parse_task_selector`) so these two tasks
could be targeted directly instead of relying on the first-N sample
order.

Command:

```
python -m src.evaluation.run_generation_diagnostics evaluation 136b0064,135a2760
```

Config: `num_predictions = 2`, `max_new_tokens = 1024`, up to
`2 * 3 = 6` sampling attempts per pair before giving up.

## Result

### 136b0064

| Split | Pair | Attempts tried | Parsed | Kept | Exact match | ADR 0009 (pre-fix) |
|---|---|---|---|---|---|---|
| train | 0 | 2 | 2 | 2 | no | 2 tried, 2 parsed, 2 kept, no |
| train | 1 | 2 | 2 | 2 | no | 6 tried, 5 parsed, 2 kept, no |
| train | 2 | 2 | 2 | 2 | no | 6 tried, 6 parsed, 2 kept, no |
| test | 0 | 2 | 2 | 2 | no | 2 tried, 2 parsed, 2 kept, no |

Parsing was already 100% pre-fix for this task. Post-fix, parsing is
still 100%, and `attempts_tried` drops to the minimum (2, matching
`num_predictions`) on every pair, where before it was 6 on two of the
four pairs. The model now produces a valid grid on its first attempt
consistently, whereas before it sometimes needed the full retry budget.
`exact_match` stays "no" on every pair, unchanged.

### 135a2760

| Split | Pair | Attempts tried | Parsed | Kept | Exact match | ADR 0009 (pre-fix) |
|---|---|---|---|---|---|---|
| train | 0 | 3 | 2 | 2 | no | 6 tried, 0 parsed, 0 kept, no |
| train | 1 | 2 | 2 | 2 | no | 6 tried, 0 parsed, 0 kept, no |
| test | 0 | 3 | 2 | 2 | no | 6 tried, 0 parsed, 0 kept, no |

Pre-fix, every pair hit the full 6-attempt budget and never parsed a
single valid grid (0/6 on all three pairs). Post-fix, every pair now
parses on 2 of 2-3 attempts. Total parsing failure is gone for this
task in this sample. `exact_match` is still "no" on every pair.

### Raw text comparison

Post-fix, a successful attempt for `135a2760` train pair 0 is a clean
rectangular grid and nothing else:

```
3333333333333
3222222222223
3213131333123
3222222222223
3333333333333
```

The one attempt that failed to parse for that same pair (attempt index
1 of 3) is not malformed digits, it is the model echoing prompt-style
labels back into its own completion:

```
3333333333333
3222222222223
3213131333123
3222222222223
3333333333333
Input:
3333333333333
...
Output:
3333333333333
...
```

(`text_to_grid` correctly rejects this, since `Input:`/`Output:` are not
all-digit lines, `_is_rectangular` never gets reached.)

Pre-fix, the equivalent stale sample on disk for the same task/pair
(`135a2760_train_0_3.txt`, ADR 0009 era, kept for comparison since the
lower attempt count post-fix did not overwrite indices 3-5) shows the
failure mode the EOS fix targeted: the completion runs into open-ended
natural-language explanation instead of stopping after the grid:

```
3333333333333
3222222222223
3213131313123
3222222222223
3333333333333
The input is a 5-line string, and the output is the same as the input
but with the third line modified. The third line in the input is
"3213131333123", and the output is "3213131313123". The difference is
in the middle part of the third line...
```

This confirms the ADR 0010 fix's intended effect (stopping generation
at a trained EOS instead of running to `max_new_tokens`) is present and
working for this task, both before and after the fix, generation used
to overrun into prose for `135a2760`, now it does not.

### Content check

For `135a2760` train pair 0, the expected output's third row is
`3213131313123`. Both parsed post-fix attempts (index 0 and 2) instead
reproduce the *input's* third row, `3213131333123`, unchanged. The model
is not applying the task's transformation, it is copying the input
through. Since `_passes_self_consistency` requires the exact expected
output to appear among a train pair's own predictions, an unmodified
copy of the input can never satisfy it, independent of parsing.

## Decision

No lever is decided here, per Golden Rule 7, this is a mechanical
diagnostic only.

The finding, on this two-task sample:

- **Parsing is no longer the bottleneck.** The task that had total
  parsing failure pre-fix (`135a2760`) now parses on every pair, and
  the task that already parsed at 100% (`136b0064`) still does, needing
  fewer attempts to get there. The ADR 0010 EOS fix's mechanism (stop
  generation at EOS instead of `max_new_tokens`) is directly visible in
  the raw text: no more open-ended prose after the grid.
- **Content is now the visible bottleneck.** Across all 7 pairs in this
  sample (train and test, both tasks), `exact_match` is "no" every
  time. For `135a2760` specifically, the parsed output is a verbatim
  copy of the input rather than the task's transformation applied to
  it, this is the mechanism behind the remaining self-consistency
  rejections in this sample, not a parsing defect.

This shifts the open question from ADR 0017 ("is it parsing or
content") toward content, on the evidence of these two tasks. It does
not by itself prove content is the *only* remaining problem across the
full sanity/evaluation set, that would need a `sanity`- or
`validation`-layer re-run of the same raw-text capture, per Golden
Rule 7.

## Consequences

- No code changes from this ADR beyond the task-id selector added to
  `run_generation_diagnostics.py` and its extraction into
  `task_selector.py` (both diagnostic tooling, no solver behavior
  change).
- CLAUDE.md Section 6 "Missing" item about diagnosing parsing-vs-content
  is now answered for this 2-task sample, next step is deciding whether
  to broaden this same raw-text capture to the full sanity/validation
  sample before picking a content-side lever (synthetic/augmented
  training data, LoRA hyperparameter tuning, or ensembling).
- No lever is picked in this ADR, that decision is explicitly deferred
  to a joint discussion, per the user's request.

## Alternatives considered

- **Run the full sanity-layer raw-text capture instead of a 2-task
  smoke sample:** rejected for now, this is mechanical debugging to
  disambiguate two known failure shapes, not a policy decision, and
  Golden Rule 7 reserves the larger sample for decisions this diagnostic
  does not make. A broader capture remains open as a possible next step
  if content-side hypotheses need more evidence.
- **Trust ADR 0017's sanity-layer accuracy result alone as sufficient
  diagnosis:** rejected, it could not distinguish parsing from content
  failure, which is exactly the ambiguity this ADR resolves for these
  two tasks.

## References

- [ADR 0009 - Empty-candidate diagnosis](0009-empty-candidate-diagnosis.md)
- [ADR 0010 - Raw generation inspection](0010-raw-generation-inspection.md)
- [ADR 0014 - OSAID-compliant base model](0014-osaid-compliant-base-model.md)
- [ADR 0015 - Layered sampling](0015-layered-sampling.md)
- [ADR 0017 - Post-EOS-fix sanity diagnosis](0017-post-eos-fix-sanity-diagnosis.md)
