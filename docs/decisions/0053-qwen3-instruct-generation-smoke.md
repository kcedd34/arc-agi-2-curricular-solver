# 0053 - Qwen3-4B-Instruct-2507 generation smoke test

Status: Informative

## Context

[ADR 0052](0052-qwen3-memory-smoke-test.md) cleared VRAM as a blocker
for `Qwen/Qwen3-4B-Instruct-2507` (ADR 0051's reverted base model).
This ADR covers ADR 0051's Step 3, tier 2: a real TTT + generation run
on `135a2760` and `136b0064` (evaluation split), the same two tasks
[ADR 0018](0018-post-eos-fix-parsing-vs-content-diagnosis.md) used for
OLMo-2, chosen for direct comparability. The goal is answering four
concrete questions before any further tier is attempted:

1. Does EOS/generation-stopping work correctly after the grid, without
   needing the [ADR 0010](0010-raw-generation-inspection.md)
   training-time EOS fix?
2. Does the [ADR 0028](0028-timing-anomaly-and-task-complexity-investigation.md)
   hallucinated-second-example pattern recur?
3. Does ADR 0028's degenerate line-repetition pattern recur?
4. Does the generated text form a valid grid on the first attempt,
   without needing multiple sampling attempts?

Per explicit standing instruction, no existing mitigation (the ADR 0010
EOS training fix, the [ADR 0029](0029-decoding-mitigations-repetition-hallucination.md)-[0032](0032-per-attempt-conditional-ngram-mitigation.md)
conditional decode escalation) is removed or disabled based on this
result alone, and no advance to Step 3 tier 3 (8-task sanity run) or
any real Kaggle GPU/leaderboard action is made from this ADR.

## Method

Unchanged from ADR 0018: `src/evaluation/generation_diagnostics.py`
(`generate_with_counts`) and
`src/evaluation/run_generation_diagnostics.py`
(`python -m src.evaluation.run_generation_diagnostics evaluation 135a2760 136b0064`)
needed no code changes, since `NeuralSolverConfig()` already reads the
active Qwen3-Instruct model (ADR 0051 Step 2). Both the aggregate
markdown table and the raw per-attempt completion text
(`outputs/raw_generations/evaluation/{task}_{split}_{pair}_{attempt}.txt`)
were captured and inspected directly, not just the aggregate metrics,
per explicit instruction. The existing ADR 0029-0032 per-attempt
conditional `no_repeat_ngram_size` escalation stayed active throughout
(not disabled), matching the current production config.

True input/output shapes for both tasks were independently confirmed
from `data/ARC-AGI-2/data/evaluation/{task}.json` to distinguish
wrong-shape/wrong-content failures from correct ones. A file-timestamp
check (`ls -la --time-style=full-iso`) confirmed that some files
present in the output directory for `136b0064` (`_train_1_2` through
`_train_1_5`, dated 2026-09-07) are stale leftovers from an earlier,
unrelated run predating this smoke test (2026-09-17), consistent with
the ADR 0009/0018-era OLMo-2 diagnostics reusing the same directory and
naming scheme; only the files dated 2026-09-17 were used as evidence.

## Result

Aggregate table (`attempts_tried` capped at 6, `_MAX_SAMPLING_ATTEMPTS_PER_PREDICTION`):

| Task | Pair | attempts_tried | num_parsed | num_kept | exact_match |
|---|---|---|---|---|---|
| 135a2760 | train 0 | 6 | 0 | 0 | no |
| 135a2760 | train 1 | 6 | 0 | 0 | no |
| 135a2760 | test 0 | 6 | 0 | 0 | no |
| 136b0064 | train 0 | 2 | 2 | 2 | no |
| 136b0064 | train 1 | 2 | 2 | 2 | no |
| 136b0064 | train 2 | 2 | 2 | 2 | no |
| 136b0064 | test 0 | 2 | 2 | 2 | no |

TTT converged normally for both tasks (135a2760: loss 0.5731 to 0.1905
over 24 steps/3 epochs, 71.04s; 136b0064: loss 0.9084 to 0.5237 over 36
steps/3 epochs, 26.45s). No tracebacks, clean run.

### Question 1: EOS/stopping

**Not resolved for free; two distinct failure modes, neither matching
OLMo-2's original problem exactly.**

- `136b0064` shows the classic non-stopping behavior in `train_0`
  attempt 0: 128 lines of `"0000000"` (correct 7-char output width,
  true row count is 15) - generation ran away instead of stopping.
- `135a2760` shows a different, Qwen3-Instruct-specific pattern on
  every pair, every attempt inspected: the grid itself is generated
  correctly (or plausibly), the model does emit *something* after it,
  but that something is natural-language commentary
  ("Explanation:", "### Step 1", LaTeX-style "boxed" answers), not a
  clean stop. The model stops the *grid* correctly but does not stop
  *generation*.

A second, previously uncharacterized pattern appears consistently
across `136b0064`'s `train_1`, `train_2`, and `test_0` pairs: attempt 0
uses the correct output width (7 chars) but overshoots the row count
(14 vs. true 7, 12 vs. true 11, 20 vs. true 19), while attempt 1 (after
the ADR 0029-0032 `no_repeat_ngram_size` escalation fires) stops at
exactly the correct row count but switches to the *wrong* width (15
chars, matching the input's width, not the output's 7). This suggests
the existing decode mitigation suppresses the pure-repetition failure
but does not fix the underlying stopping/content problem, it just
changes which dimension (row count vs. column width) comes out wrong.

Conclusion: the ADR 0010 training-time EOS fix and the ADR 0029-0032
decode mitigations both still address real, reproducible failure modes
on Qwen3-Instruct. Neither should be removed.

### Question 2: hallucinated second example (ADR 0028)

**Recurs.** `135a2760_train_0_0.txt` shows 5 correct grid rows, a blank
line, then a full fabricated second `Input:`/`Output:` example (lines
7-26), before the model moves into free-text analysis.

### Question 3: degenerate line repetition (ADR 0028)

**Recurs, plus a new variant not seen with OLMo-2.**

- Classic grid-line repetition: `136b0064_train_0_0.txt`, 128 lines of
  literally `"0000000"` versus a true, non-trivial 15-row output
  (confirmed non-zero from the task JSON).
- New variant, degenerate repetition of natural-language text rather
  than grid lines: `135a2760_train_0_1.txt`, after 4 correct-looking
  grid rows, the exact same explanatory sentence repeats verbatim
  roughly 20 times, cut off mid-sentence. The ADR 0029-0032 mitigations
  target `no_repeat_ngram_size` at the token level and did fire on this
  task's later attempts, but this specific attempt still shows the
  pattern, since a single long repeated sentence is a different
  repetition signature than a short repeated grid line.

Two more Qwen3-Instruct-specific artifacts, not part of OLMo-2's
original diagnostic vocabulary (ADR 0010/0028), were observed in
`135a2760`'s free-text tails:
- `135a2760_test_0_3.txt`: a fabricated `### Final Answer:\n\boxed{...}`
  LaTeX-style block after the correct grid and explanation, suggesting
  math/reasoning post-training bleeding into non-math grid completion.
- `135a2760_test_0_5.txt`: near-duplicate (not verbatim-identical)
  repeated short sentences ("The output is the same as the input" /
  "identical" / "equal", reworded each time) - a softer degenerate
  pattern than exact repetition, likely harder for an n-gram-based
  mitigation to catch.

### Question 4: first-attempt parsing success

**No, for both tasks, in different ways.**

- `135a2760`: 0/6 attempts parsed on all 3 pairs (`num_parsed=0`
  despite visually-correct grid content preceding the rambling tail),
  consistent with the parser requiring the completion to reduce
  cleanly to a grid with no significant trailing non-grid content.
- `136b0064`: `num_parsed=2/2` on all 4 pairs, but this "success" is
  misleading: both accepted attempts are wrong-shape or wrong-content
  all-zero grids (confirmed against real train-pair ground truth,
  e.g. `136b0064`'s true train-pair-0 output is a real, non-trivial
  15x7 grid, not all zeros). The parser accepts any well-formed
  rectangular text block, correctness is a separate, unevaluated axis
  at this stage of the pipeline (self-consistency/exact-match handles
  that later, and both pairs still show `exact_match=no`).

## Decision

Proceeds no further than this diagnostic. Per the standing instruction:

- The ADR 0010 EOS training fix and the ADR 0029-0032 conditional
  decode mitigations stay active and unmodified; this result gives
  concrete evidence they are still needed, not that they are
  sufficient.
- Step 3 tier 3 (8-task sanity run) is not started from this ADR.
- No real Kaggle GPU round or leaderboard submission is proposed or
  triggered from this ADR.

This result should be reviewed before deciding whether tier 3 is worth
running as-is, or whether Qwen3-Instruct's new failure modes
(rambling natural-language tails, sentence-level repetition, fabricated
boxed-answer blocks) warrant a targeted mitigation first.

## Consequences

- No code changes; diagnostic only, same scope as ADR 0016/0018/0052.
- Confirms Qwen3-Instruct does not "solve EOS for free" relative to
  OLMo-2: it trades one failure shape (silent runaway repetition) for
  a mix of the same failure plus a new one (correct grid followed by
  natural-language continuation), consistent with it being an
  instruction/chat-tuned model rather than OLMo-2's base checkpoint.
- Identifies three new failure-mode categories not covered by the
  existing ADR 0028-0032 diagnostic vocabulary or mitigations:
  natural-language chain-of-thought tails after a correct grid,
  sentence-level (not line-level) degenerate repetition, and fabricated
  LaTeX/boxed-answer blocks. None of these are addressed by the current
  `no_repeat_ngram_size`/`repetition_penalty`/stop-on-second-`Input:`
  mitigations, which were designed against OLMo-2's grid-line-level
  failure signatures.
- Confirms (file-timestamp check) that `outputs/raw_generations/` and
  `outputs/diagnostics/generation_counts/` accumulate stale files
  across unrelated runs sharing the same task id and split; any future
  reuse of this directory for diagnosis should check modification
  times before trusting file presence alone.
- Open question, not investigated here: whether a stricter stop
  condition (e.g. stopping generation immediately once a well-formed
  grid block closes, independent of EOS) would address the
  natural-language-tail pattern without the training-time cost of a
  new EOS fix.

## Alternatives considered

- **Treat `136b0064`'s `num_parsed=2/2` as evidence question 4 is
  answered "yes":** rejected; the raw text shows both accepted
  completions are wrong-shape/wrong-content, so aggregate parse counts
  alone are misleading without direct raw-text inspection, exactly the
  reason the user required capturing raw text in the first place.
- **Extend this smoke test with more attempts/tasks before writing the
  ADR:** rejected for now; the patterns recur consistently across every
  attempt inspected for both tasks (at least 2 per pair, up to 6), and
  the explicit instruction caps this tier at 1-2 tasks: a broader
  sample belongs to tier 3, not this tier.

## References

- [ADR 0010 - Raw generation inspection](0010-raw-generation-inspection.md)
- [ADR 0018 - Post-EOS-fix parsing-vs-content diagnosis](0018-post-eos-fix-parsing-vs-content-diagnosis.md)
- [ADR 0028 - Timing anomaly and task complexity investigation](0028-timing-anomaly-and-task-complexity-investigation.md)
- [ADR 0029 - Decoding mitigations for repetition and hallucination](0029-decoding-mitigations-repetition-hallucination.md)
- [ADR 0032 - Per-attempt conditional no_repeat_ngram_size mitigation](0032-per-attempt-conditional-ngram-mitigation.md)
- [ADR 0051 - Revert base model to Qwen3-4B-Instruct-2507, accepted-risk decision](0051-reversao-para-qwen3-risco-aceito.md)
- [ADR 0052 - Qwen3-4B-Instruct-2507 memory smoke test](0052-qwen3-memory-smoke-test.md)
