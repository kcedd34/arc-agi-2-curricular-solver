# 0024 - Shape mismatch root cause diagnosis

Status: Informative

## Context

ADR 0023 found that 10 of 11 held-out test pairs (sanity layer, same 8
tasks as ADR 0017/0018/0019/0021) have a kept prediction whose output
grid *shape* does not match the expected shape, a more basic gap than
the content bottleneck ADR 0018-0022 have been discussing. Before
choosing between the two content-side levers already on the table
(color augmentation, ADR 0020/0021; cross-task pretraining, ADR 0022),
this needs its own root cause, since a content fix does not help if the
basic shape is already wrong.

Three candidate explanations, tested against the same 10 mismatched
pairs:

1. The task's output-size rule is genuinely variable/content-dependent
   (hard to derive), not a fixed or input-shape-derived rule.
2. The model is copying a size it saw during this task's own TTT
   (a train pair's output shape), a structural parallel to the content
   copy-paste ADR 0018/0023 already found, but in the grid dimension.
3. Generation stopped prematurely (EOS fired before enough rows were
   emitted), the mirror-image of ADR 0010's original problem (EOS never
   fired, ran to the cap).

## Method

No GPU/model re-run, per explicit instruction. Two small scripts, both
reusing artifacts already persisted by the ADR 0023 run:

- `src/evaluation/analyze_shape_mismatch.py` (host Python, no
  `unsloth` dependency): loads the 8 tasks via `task_loader.load_task`,
  classifies each task's train-pair output shapes as fixed or variable
  and checks whether output shape always equals input shape; reparses
  every raw `.txt` completion for each mismatched test pair via
  `grid_serialization.text_to_grid`, replaying the same first-parsed,
  dedup-by-distinct-grid logic `generation_diagnostics.generate_with_counts`
  uses in production, to reconstruct exactly which attempt(s) produced
  the kept prediction(s) and their shape; checks each kept prediction's
  shape against every train-pair output shape via the existing
  `pair_diagnostics.dimension_match` (question 2).
- `src/evaluation/analyze_shape_mismatch_tokens.py` (WSL venv, loads
  only `AutoTokenizer.from_pretrained("allenai/OLMo-2-1124-7B")`, no
  model/GPU): the tokenizer files were already cached locally from
  prior real runs (`~/.cache/huggingface/hub/models--allenai--OLMo-2-1124-7B`),
  so this needed no new download. Retokenizes each identified kept
  prediction's raw completion text and compares the token count against
  `max_new_tokens` (1024, see `NeuralSolverConfig`). `_generate_completion`
  decodes with `skip_special_tokens=True`, so the EOS token itself is
  never present in the saved text; a token count well under the cap
  means generation must have stopped before reaching `max_new_tokens`,
  i.e. via EOS, while a count at or near the cap means the cap was
  almost certainly hit instead (question 3).

## Result

One row per shape-mismatched test pair (kept-prediction attempts shown
together); `16de56c4` test-0, the one pair whose shape already matched
in ADR 0023, is included at the end for contrast, not counted as a
mismatch.

| Task | Size rule (from train pairs) | Test pair | Expected shape | Predicted shapes (attempt) | Row width (cols) matches expected | Matches a train-output shape | Tokens used / cap (1024) |
|---|---|---|---|---|---|---|---|
| `0934a4d8` | variable, **not** derivable from input shape (input fixed 30x30 every train pair, outputs vary: (9,4),(4,5),(3,7),(4,4), content-dependent) | test-0 | (9,3) | (2,3) attempt0; (7,4) attempt1 | yes (attempt0); no, off by +1 (attempt1) | no / no | 3; 20 |
| `135a2760` | variable, output = input shape exactly ((5,13) and (21,22) across train) | test-0 | (29,29) | (17,29) attempt0; (15,29) attempt1 | yes; yes | no; no | 186; 164 |
| `136b0064` | variable, rows = input rows, cols fixed at 7 ((15,7),(7,7),(11,7)) | test-0 | (19,7) | (9,6) attempt0; (13,15) attempt1 | no, off by -1; no, off by +8 (13,15 matches the *input's own* width of 15, not the output width) | no; no | 26; 77 |
| `13e47133` | variable, output = input shape exactly ((20,20),(20,20),(10,13)) | test-0 | (30,30) | (19,30) attempt2; (19,30) attempt4 (identical) | yes; yes | no; no | 208; 208 |
| `13e47133` | (same task) | test-1 | (30,30) | (48,30) attempt2 (overshoot); (1,31) attempt3 (degenerate) | yes; no, off by +1 | no; no | 527; 11 |
| `142ca369` | variable, output = input shape exactly ((20,20),(18,18),(20,20)) | test-0 | (18,18) | (21,18) attempt0 (overshoot); (17,18) attempt1 | yes; yes | no; no | 146; 118 |
| `142ca369` | (same task) | test-1 | (20,19) | (17,19) attempt0; (36,19) attempt1 (overshoot) | yes; yes | no; no | 135; 287 |
| `16b78196` | **fixed**, (30,30) both train pairs, also equals input shape | test-0 | (30,30) | (14,30) attempt0; (17,30) attempt2 | yes; yes | no; no | 153; 186 |
| `16de56c4` | variable, output = input shape exactly ((12,9),(9,20),(7,15)) | test-1 | (9,21) | (11,21) attempt1 (overshoot); (8,21) attempt2 | yes; yes | no; no | 87; 63 |
| `1818057f` | variable, output = input shape exactly ((10,12),(15,17),(12,12)) | test-0 | (22,22) | (20,22) attempt0; (17,22) attempt1 | yes; yes | no; no | 179; 152 |
| `16de56c4` (contrast, shape already matched) | variable, output = input shape | test-0 | (9,21) | (9,21) attempt1 (exact); (8,21) attempt2 | yes; yes | no; no | 71; 63 |

Task-level size-rule summary (all 8 tasks, including the one held-out
pair that already matched):

| Size rule category | Tasks |
|---|---|
| Output shape always equals input shape | `135a2760`, `13e47133`, `142ca369`, `16de56c4`, `1818057f` (5/8) |
| Output shape derivable from input shape by a simple partial rule (rows = input rows, cols fixed) | `136b0064` (1/8) |
| Output shape fixed regardless of input (and happens to equal input shape too) | `16b78196` (1/8) |
| Output shape variable and **not** derivable from input shape alone (genuinely content-dependent) | `0934a4d8` (1/8) |

## Answering the three questions

**(1) Is the size rule fixed or variable?** Mostly variable, but
**derivable from the input's own shape in 7 of 8 tasks** (5 "output =
input" exactly, 1 partial rule, 1 fixed-and-also-equal-to-input). Only
`0934a4d8` requires real content-dependent reasoning to get the size
right. So a hard/unlearnable size rule is not the dominant explanation:
in most of these tasks the correct shape was, in principle, the
cheapest possible rule to apply ("match the input you were just given"),
and it was still wrong on every single held-out pair.

**(2) Does the predicted shape match a train-output shape (copying a
seen size)?** No evidence anywhere. **0 of 22** kept-prediction shapes
across all 10 mismatched test pairs match any of that task's own
train-pair output shapes. This structural parallel to the content
copy-paste pattern is **refuted** at this sample size, not confirmed.

**(3) Did generation stop via EOS or hit the token cap?** Via EOS,
consistently. **All 22 of 22** kept-prediction completions retokenize to
well under the 1024-token cap (3 to 527 tokens, most under 300). The
token budget was never the constraint; generation always stopped
because EOS fired, just not always at the row count the task actually
needed.

## Cross-cutting signal not directly asked for, but the clearest pattern in this data

Splitting "shape" into its two components (row count vs. row width)
shows the failure is concentrated almost entirely in **row count**, not
row width: **18 of 22** kept predictions have the exact expected number
of columns per row, while only **1 of 22** also has the exact expected
number of rows (the one pair ADR 0023 already flagged as a shape match).
Undershooting the row count (stopping too early) is more common (14 of
22 mismatched attempts) than overshooting (4 of 22), with `136b0064`
and `0934a4d8` the only cases where column width is also wrong.

This means the per-row format (how wide a row is, when to end a row
with a newline) is being learned and reproduced correctly almost every
time; the specific thing going wrong is deciding **how many rows to
emit before stopping**, and stopping there is a genuine EOS emission,
not a truncation artifact of the generation budget.

## Decision

No lever is decided here, per the explicit instruction this
investigation was requested under. This is a diagnostic result only,
per Golden Rule 7.

## Consequences

- Rules out "the task's size rule is too hard to learn" as the
  dominant explanation: 7 of 8 tasks have a size rule at least as
  simple as "match the input's shape", yet still fail on every held-out
  pair.
- Rules out "copying a previously-seen training shape" entirely at this
  sample size (0/22), so this is not a structural sibling of the
  content copy-paste pattern in the way ADR 0021/0023 found for
  content.
- Confirms the failure is a premature/inconsistent **EOS emission in
  the row dimension**, well within token budget, not a token-cap
  truncation. This is a genuine sibling of ADR 0010's problem, but in
  the opposite direction (ADR 0010: EOS never fires, runs to the cap;
  here: EOS fires, but not always at the row count the task needs).
- Adds a sharper diagnostic signal than "shape is wrong": row *width*
  is reliably correct (18/22), row *count* is the near-exclusive
  failure point. Any future fix targeting shape specifically should
  aim at row-count control (e.g., explicit row-count conditioning,
  reinforcing "stop after exactly N rows" during TTT) rather than
  format/parsing, which already works.
- This shape-level finding is orthogonal to, and should be resolved
  independently of, the still-open content-level lever choice (color
  augmentation vs. cross-task pretraining, ADR 0022): fixing content
  does not fix row-count control, and vice versa.

## Alternatives considered

- **Approximate token usage from raw-text character length instead of
  retokenizing:** rejected. The OLMo tokenizer was already cached
  locally in the WSL venv from prior real runs (no new download
  needed), so exact token counts were available for the same cost as
  an approximation, with no ambiguity from BPE merging multi-digit
  runs into single tokens.
- **Decide a fix now (e.g., row-count conditioning) based on this
  result:** rejected per the user's explicit instruction; this ADR
  presents the pattern for a joint decision, it does not make one.

## References

- [ADR 0010 - Raw generation inspection](0010-raw-generation-inspection.md)
- [ADR 0015 - Layered sampling](0015-layered-sampling.md)
- [ADR 0020 - Next accuracy lever: data augmentation, not hyperparameter tuning](0020-lever-decision-data-augmentation.md)
- [ADR 0021 - Geometric augmentation smoke test](0021-augmentation-geometric-smoke-test.md)
- [ADR 0022 - Hypothesis reformulation after the pre-existing-augmentation discovery](0022-hypothesis-reformulation-post-augmentation-discovery.md)
- [ADR 0023 - Sanity run of the current mature config, post-augmentation](0023-sanity-current-config-post-augmentation.md)
