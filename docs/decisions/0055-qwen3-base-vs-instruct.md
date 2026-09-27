# 0055 - Qwen3-4B-Base vs Instruct: is the reasoning habit post-training-specific?

Status: Informative

## Context

[ADR 0053](0053-qwen3-instruct-generation-smoke.md) and
[ADR 0054](0054-formato-chat-template-qwen3.md) both found that
`Qwen/Qwen3-4B-Instruct-2507` exhibits a reasoning-adjacent habit
(chain-of-thought text appearing unprompted, at times replacing the
grid entirely) that survives an explicit system-prompt instruction not
to reason. Before investing in a new decode-level mitigation for this
specific behavior, the governing hypothesis to test: is this habit tied
to the **Instruct** post-training (RL/instruction-tuning to "think
before answering"), and therefore absent from the **Base** variant,
same family and size? This would be consistent with this project's own
OLMo-2 experience: once EOS was fixed ([ADR 0010](0010-raw-generation-inspection.md)),
the Base checkpoint behaved as pattern continuation, with no spontaneous
commentary or reasoning.

If confirmed, the already-validated OLMo-2 mitigations (ADR 0010's EOS
fix, ADR 0029-0032's conditional decode mitigation) become directly
reusable, adapted to Qwen3-4B-Base, instead of requiring a new
mitigation built specifically for Instruct's failure modes. If refuted,
decode-level mitigation for Instruct's own failure modes becomes the
next lever.

## Method

1. Swapped `NeuralSolverConfig.model_name` (`src/solvers/neural/config.py`)
   from `Qwen/Qwen3-4B-Instruct-2507` to `Qwen/Qwen3-4B-Base`, the only
   code change required, framed as temporary/reversible in the module
   docstring. No other config field changed.
2. Ran the same memory smoke test as ADR 0052 (task `d8e07eb2`, the
   worst case by total grid cells) to confirm the swap does not
   regress VRAM usage.
3. Ran the same generation smoke test as ADR 0053/0054 (tasks
   `135a2760`, `136b0064`, `python -m src.evaluation.run_generation_diagnostics evaluation 135a2760,136b0064`),
   the production raw-completion-prompt diagnostic path (not the
   chat-template path from ADR 0054, since Base has no chat turn
   structure to speak of). All 30 pre-existing files for these two
   tasks in `outputs/raw_generations/evaluation/` were moved to a
   `_pre_adr0055_backup/` subdirectory beforehand, so every file found
   afterward is genuinely from this run.
4. Inspected the aggregate attempt/parse table and the raw completion
   text of all 17 files produced (both held-out test pairs in full,
   plus 8 of 10 training pairs), following this project's standing
   practice of not trusting aggregate counts alone.

## Result

### Tier 1: memory smoke test

No OOM at any step. Peak VRAM 5.26 GiB of 8.00 GiB (headroom 2.74 GiB),
slightly higher than Instruct's 4.41 GiB (ADR 0052) but well within
budget. TTT ran 3 epochs/60 steps, loss 0.34 to 0.09, `train_runtime=177s`.
Memory is not a blocker for Base, same conclusion as for Instruct.

### Tier 2: generation smoke test

Aggregate table:

| Task | Split | Pair | Attempts tried | Parsed | Kept | Exact match |
|---|---|---|---|---|---|---|
| 135a2760 | train | 0 | 2 | 2 | 2 | yes |
| 135a2760 | train | 1 | 4 | 3 | 2 | no |
| 135a2760 | test | 0 | 3 | 2 | 2 | no |
| 136b0064 | train | 0 | 2 | 2 | 2 | no |
| 136b0064 | train | 1 | 2 | 2 | 2 | no |
| 136b0064 | train | 2 | 2 | 2 | 2 | no |
| 136b0064 | test | 0 | 2 | 2 | 2 | no |

TTT: `135a2760` 24 steps/3 epochs, `train_runtime=65.43s`,
`train_loss=0.2304`; `136b0064` 36 steps/3 epochs,
`train_runtime=26.08s`, `train_loss=0.6157`. No OOM, no crash, no
exceptions.

Raw-text inspection, all 17 files:

- **`135a2760_test_0_0.txt`**: a complete, well-formed 29-row grid,
  followed by a trailing hallucination unrelated to the ARC task
  entirely ("Sure! Here is the Python code that inverts an 8 x 8
  matrix:" plus a Python function definition, cut off mid-token at the
  1024-token cap). A new failure mode, not previously documented in
  ADR 0028/0053/0054.
- **`135a2760_test_0_1.txt`**, **`135a2760_test_0_2.txt`**: clean,
  well-formed grid only, no trailing text of any kind.
- **`136b0064_test_0_0.txt`**: a small, clean, well-formed 7x9 grid, no
  issues.
- **`136b0064_test_0_1.txt`**: starts with a plausible small grid, then
  degenerates into runaway `0000000` line repetition to the token cap.
- **`135a2760_train_0_0.txt`**, **`135a2760_train_0_1.txt`**,
  **`136b0064_train_0_0.txt`**: clean small grids, no issues.
- **`135a2760_train_1_0.txt`**: degenerate repetition, an extremely
  long run of the character `4`, then a repeating `4222222222222222222224`
  sub-pattern, to the token cap.
- **`136b0064_train_0_1.txt`**, **`136b0064_train_1_1.txt`**: start
  plausible, then degenerate into runaway all-zero-row repetition to
  the token cap.

None of the 17 files inspected show step-by-step reasoning about the
ARC task (no "let me check if this is a reflection", no row-by-row
symmetry narration, no fabricated `\boxed{...}` block), the pattern
that defined ADR 0053/0054's most severe failure mode.

### Answering the three governing questions

**1. Does the reasoning/commentary habit disappear?** Largely yes, with
one nuance. The specific pattern from ADR 0053/0054 (natural-language
commentary or full chain-of-thought about solving the grid task) was
not observed in any of the 17 files. The one aberration found
(`135a2760_test_0_0.txt`'s Python-matrix-inversion tangent) is
structurally different: it is not reasoning about the ARC task at all,
it is an unrelated topic drift, closer to a base model's raw
"what plausibly follows this text" continuation than to Instruct's
directed, task-aware reasoning trace. This is consistent with the
hypothesis: the task-reasoning takeover behavior is absent, though Base
is not entirely free of post-grid hallucinated continuations in
general.

**2. Does degenerate line-level repetition still appear?** Yes, clearly
confirmed present, recurring across both training and held-out pairs on
both tasks (`135a2760_train_1_0`, `136b0064_test_0_1`,
`136b0064_train_0_1`, `136b0064_train_1_1`), matching ADR 0028's exact
pattern (all-zero-row runaway repetition, character-level runaway
repetition, sub-pattern runaway repetition). This confirms the
governing instruction's own expectation that this failure mode is not
tied to the Instruct variant.

**3. Does first-attempt parsing improve?** Yes, materially, with one
recurring caveat. Every pair here parses within 2-4 attempts, a sharp
contrast to ADR 0053's `135a2760` test pair (0/6 parsed despite visible
correct grid content) and its `136b0064` test pair's misleading "2/2
parsed" despite wrong-shape/wrong-content all-zero grids. That same
misleading-parse issue recurs identically here: `136b0064` test 0 is
reported `parsed=2, kept=2`, but one of the two saved completions
(`136b0064_test_0_1.txt`) is the degenerate all-zero-repetition
pattern, not a genuinely useful prediction. So the parsing-rate
improvement is real for `135a2760`, but `136b0064`'s specific
parser-leniency issue is unchanged by the model swap.

## Decision

The hypothesis is **confirmed, with a documented nuance**: swapping
from `Qwen/Qwen3-4B-Instruct-2507` to `Qwen/Qwen3-4B-Base` removes the
task-directed reasoning/chain-of-thought takeover behavior that defined
ADR 0053/0054's most severe failure mode, while leaving ADR 0028's
already-known, Instruct-independent degenerate-repetition failure mode
unchanged, exactly as anticipated. First-attempt parsing also improves
materially, though not completely (the `136b0064` misleading-parse
issue persists).

Per the governing instruction, this reopens the more direct
mitigation path: applying the already-validated OLMo-2 mitigations
(ADR 0010's EOS fix, ADR 0029-0032's conditional decode mitigation),
adapted to Qwen3-4B-Base, is now the next candidate lever, in place of
building a new mitigation for a behavior that turns out to be specific
to the Instruct checkpoint. This ADR does not decide or implement that
adaptation; it is itself a new lever requiring its own decision before
implementation (Golden Rule 1).

- `model_name` stays at `Qwen/Qwen3-4B-Base` for now, since it is the
  variant this ADR's evidence supports continuing with; the config
  docstring should be updated to reflect this decision rather than the
  prior "revert if refuted" framing.
- No mitigation removed: ADR 0010's EOS fix and ADR 0029-0032's decode
  mitigations stay active and unmodified (and were, in fact, already
  exercised during this run, since `run_generation_diagnostics.py`
  uses the same production generation path with
  `enable_conditional_escalation=True` by default).
- Step 3 tier 3 (8-task sanity run) is not started from this ADR.
- No real Kaggle GPU round or leaderboard submission is proposed or
  triggered from this ADR.

## Consequences

- Answers the governing prompt's hypothesis directly: the task-reasoning
  takeover behavior is Instruct-specific, not a Qwen3-4B-family-wide
  trait; the degenerate-repetition behavior is architecture/training-
  data-level, not post-training-specific.
- The new hallucinated-tangent failure mode found here
  (`135a2760_test_0_0.txt`) is not covered by any existing ADR
  0029-0032 mitigation (those target grid-line-level repetition
  signatures, not unrelated topic drift) or by ADR 0053/0054's three
  named Instruct failure modes. It is a fourth, distinct pattern worth
  naming for any future mitigation design, though on a single
  occurrence in a small sample it is not yet characterized at
  `sanity`/`validation` scale.
- `136b0064`'s misleading-parse issue (a structurally well-formed but
  content-degenerate grid counted as "parsed") is a parser-leniency
  gap independent of the model choice; worth a dedicated look before or
  alongside any future decode-mitigation work, though not scoped or
  decided here.
- Whether to adapt ADR 0010/0029-0032 to Qwen3-4B-Base, and in what
  form, is an open joint call, to be documented in its own ADR before
  implementation, per the governing instruction's own branching logic.

## Alternatives considered

- **Treat the single hallucinated-tangent occurrence as disproof of the
  hypothesis:** rejected; the pattern is structurally different from
  Instruct's task-directed reasoning takeover (it never reasons about
  the grid task, it drifts to an unrelated topic), and none of the
  other 16 files inspected show any comparable pattern. Recording it
  as a distinct, minor caveat is more honest than either ignoring it or
  overweighting a single instance.
- **Run a larger sample before concluding:** rejected for this tier,
  consistent with ADR 0053/0054's own scope (1-2 tasks is the `smoke`
  tier, per Golden Rule 7); a broader confirmation belongs to tier 3
  (8-task sanity) or a future `validation`-tier run, not this
  diagnostic.
- **Proceed directly to designing the OLMo-2-mitigation adaptation in
  this same ADR:** rejected; per Golden Rule 1, that is a separate
  implementation decision needing its own ADR, and the governing
  instruction only asked this one to resolve the Base-vs-Instruct
  hypothesis.

## References

- [ADR 0010 - Raw generation inspection](0010-raw-generation-inspection.md)
- [ADR 0028 - Timing anomaly and task complexity investigation](0028-timing-anomaly-and-task-complexity-investigation.md)
- [ADR 0029 - Decoding mitigations for repetition and hallucination](0029-decoding-mitigations-repetition-hallucination.md)
- [ADR 0032 - Per-attempt conditional no_repeat_ngram_size mitigation](0032-per-attempt-conditional-ngram-mitigation.md)
- [ADR 0051 - Revert base model to Qwen3-4B-Instruct-2507, accepted-risk decision](0051-reversao-para-qwen3-risco-aceito.md)
- [ADR 0053 - Qwen3-4B-Instruct-2507 generation smoke test](0053-qwen3-instruct-generation-smoke.md)
- [ADR 0054 - Chat-template prompt format test for Qwen3-Instruct's new failure modes](0054-formato-chat-template-qwen3.md)
