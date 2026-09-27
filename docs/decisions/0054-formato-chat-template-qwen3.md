# 0054 - Chat-template prompt format test for Qwen3-Instruct's new failure modes

Status: Informative

## Context

The governing hypothesis for this investigation: the three new failure
modes [ADR 0053](0053-qwen3-instruct-generation-smoke.md) found on
`Qwen/Qwen3-4B-Instruct-2507` (chain-of-thought tails after a correct
grid, sentence-level repetition, fabricated `\boxed{...}` blocks) are
the Qwen3 family's characteristic "thinking"/reasoning behavior, not a
random artifact, and might have a root-cause fix via prompt format
rather than via decoding parameters.

Two things were established before any new code was written:

1. `Qwen/Qwen3-4B-Instruct-2507` is a non-thinking-only checkpoint, so
   the literal `/no_think`/`enable_thinking=False` mechanism (built for
   Qwen3's hybrid-thinking variants) does not apply here; there is no
   such flag to flip.
2. The production pipeline never calls
   `tokenizer.apply_chat_template` anywhere in `src/`: it feeds a raw,
   completion-style prompt (`prompt_builder.py`) to a model that was
   instruction/chat-tuned to expect turn-structured input
   (`<|im_start|>role ... <|im_end|>`). This is a real, plausible
   confound: an instruction-tuned model given a non-chat-shaped prompt
   may produce less predictable stopping behavior than the same model
   given its native format.

Per the standing instruction, this ADR tests hypothesis 2 (a prompt-
format fix) before considering any new decode-level mitigation, and
must inspect raw generated text directly, not just aggregate counts,
to answer ADR 0053's four questions.

## Method

New diagnostic-only modules (no production code changed):

- `src/solvers/neural/chat_prompt_builder.py`: builds a system/user/
  assistant chat turn structure via `tokenizer.apply_chat_template`,
  with an explicit system prompt instructing the model to respond with
  only the grid and no explanation, reasoning, or extra text.
- `src/evaluation/chat_template_generation_diagnostics.py`: mirrors
  `ttt_trainer.py`/`generation_diagnostics.py`'s TTT and sampling-loop
  logic unchanged, only the prompt text fed to the tokenizer differs.
- `src/evaluation/run_chat_template_diagnostics.py`: CLI runner,
  mirrors `run_generation_diagnostics.py`'s structure and output
  format so the two are directly comparable.

Real GPU run (WSL2, RTX 4060 Ti), same two tasks and split as ADR 0053
for direct comparability:

```
python -m src.evaluation.run_chat_template_diagnostics evaluation 135a2760,136b0064
```

Both the aggregate table and every raw per-attempt completion
(`outputs/raw_generations_chat_template/evaluation/{task}_{split}_{pair}_{attempt}.txt`)
were captured and inspected directly. File modification timestamps
were checked first: all files in this run's output directory carry the
same run's timestamps (a brand-new, dedicated directory with no prior
runs), so the stale-file risk ADR 0053 flagged for the shared
`outputs/raw_generations/` directory does not apply here.

## Result

Aggregate table (`attempts_tried` capped at 6):

| Task | Split | Pair | Attempts tried | Parsed | Kept | Exact match |
|---|---|---|---|---|---|---|
| 135a2760 | train | 0 | 5 | 2 | 2 | no |
| 135a2760 | train | 1 | 6 | 0 | 0 | no |
| 135a2760 | test | 0 | 6 | 0 | 0 | no |
| 136b0064 | train | 0 | 6 | 1 | 1 | no |
| 136b0064 | train | 1 | 6 | 1 | 1 | no |
| 136b0064 | train | 2 | 6 | 0 | 0 | no |
| 136b0064 | test | 0 | 6 | 0 | 0 | no |

TTT converged normally for both tasks (135a2760: 24 steps/3 epochs,
`train_runtime=59.32s`, loss 2.14 to 0.19-0.29 with noisy spikes;
136b0064: 36 steps/3 epochs, `train_runtime=29.15s`, loss 1.87 to
0.52-0.58). No OOM, no crash, no exceptions. The ADR 0036 timing
anomaly previously observed on `135a2760` (~5000s) did not recur; the
whole run finished in well under 20 minutes.

Both held-out test pairs (the ones that matter most for this
comparison) show total parsing failure, 0/6, unchanged from ADR 0053's
own held-out result on `135a2760` test 0 and worse than ADR 0053's
misleading 2/2 on `136b0064` test 0.

### Question 1: EOS/stopping and the three named failure modes

**Not resolved; one target failure mode disappears, but is replaced by
a new, more severe failure mode.**

- **Commentary tail after a correct grid:** not observed in any file
  inspected. When a grid is emitted at all
  (`135a2760_train_0_{0,1}.txt`), the completion is grid-only, no
  trailing natural-language text. The explicit system-prompt
  instruction does appear to suppress this specific pattern.
- **New failure mode, not seen under the raw completion-style prompt:
  full chain-of-thought reasoning text, zero grid content.**
  `135a2760_test_0_0.txt`, `135a2760_test_0_2.txt`,
  `135a2760_train_1_0.txt`, and `136b0064_train_0_0.txt` all show the
  model narrating step-by-step analysis ("Let me check if this is a
  reflection...", "Let me rotate the grid 180 degrees...", row-by-row
  symmetry checks) that never converges to a grid before being cut off
  mid-sentence at the token budget. This happens despite the system
  prompt explicitly stating: "Do not include any explanation,
  reasoning, or text of any kind besides the grid." The model ignores
  this instruction in a substantial fraction of attempts (at least 2/6
  on the `135a2760` test pair alone). This is direct evidence that the
  reasoning tendency is not controllable via prompt instruction, and
  that giving the model its native chat-turn structure does not
  suppress it, if anything it seems to invite it more than the raw
  completion format did.
- **Sentence/line-level degenerate repetition (ADR 0028):** recurs
  unchanged. `135a2760_test_0_{1,3,4,5}.txt` all show the exact same
  30-character grid line repeated 28-32 times. `136b0064`'s test and
  train pairs collapse into a different degenerate pattern: an all-zero
  block with inconsistent row lengths (`136b0064_test_0_{0,1}.txt`,
  `136b0064_train_0_{1,2}.txt`), which fails to parse as a valid grid
  outright (structurally, not just on content).
- **Fabricated `\boxed{...}` block:** not observed in any of the 12
  files inspected in this sample. Not enough evidence to say it is
  resolved (small sample), only that it did not recur here.

### Question 2/3: hallucinated example, degenerate repetition (ADR 0028)

Degenerate line-level repetition recurs identically to ADR 0053 (see
above). No hallucinated second `Input:`/`Output:` example was observed
in this sample, though again the sample is small.

### Question 4: first-attempt parsing success

**No, and arguably worse than ADR 0053's raw completion format.** Both
held-out test pairs show 0/6 parsed. The one qualitative improvement
(clean grid-only output with no commentary tail, when a grid is
produced at all) is outweighed by a lower overall grid-emission rate:
under the chat template, a meaningful share of attempts produce no grid
at all, only reasoning text or degenerate collapse.

## Decision

The prompt-format hypothesis is rejected as a root-cause fix for these
failure modes:

- The literal thinking-mode-suppression mechanism does not apply
  (confirmed before this ADR: the model is non-thinking-only).
- Feeding the model its native chat-turn structure, with an explicit
  system-prompt instruction against reasoning/explanation, does not
  resolve ADR 0053's failure modes. It eliminates one specific pattern
  (commentary appended after a correct grid) but surfaces a new,
  arguably more severe one (full chain-of-thought reasoning replacing
  the grid entirely, ignoring an explicit instruction not to reason),
  and leaves degenerate repetition unchanged.
- This is itself informative evidence for the original hypothesis: the
  behavior does look like the Qwen3 family's characteristic reasoning
  tendency (the model narrates analysis unprompted, in the same style
  as a "thinking" trace, and gets cut off mid-analysis exactly like an
  exhausted reasoning budget would), but there is no simple prompt-level
  off-switch for it on this checkpoint.

Per the standing instruction, since the cause is not resolvable via
prompt, a decode-level mitigation may now be considered, but that
mitigation itself is a new lever requiring its own decision before
implementation (Golden Rule 1), not decided by this ADR. No mitigation
is implemented here.

- The ADR 0010 EOS fix and ADR 0029-0032 decode mitigations stay
  active and unmodified.
- `chat_prompt_builder.py` and the diagnostic modules built for this
  ADR stay diagnostic-only; not wired into `neural_solver.py` or
  `run_neural.py`.
- Step 3 tier 3 (8-task sanity run) is not started from this ADR.
- No real Kaggle GPU round or leaderboard submission is proposed or
  triggered from this ADR.

## Consequences

- Closes the specific investigation opened by the governing prompt:
  both the thinking-mode-flag question and the prompt-format hypothesis
  are now answered, negatively, with real GPU evidence.
- Whether to build a decode-level mitigation targeting these three
  failure modes (chain-of-thought/reasoning takeover, sentence-level
  repetition, fabricated boxed blocks), and if so what shape it takes,
  is an open joint call, analogous to the ADR 0029-0032 mitigation
  chain built for OLMo-2/ADR 0028's failure modes. The existing
  `no_repeat_ngram_size`/`repetition_penalty` mitigations were designed
  against grid-line-level repetition signatures and do not address a
  completion that never contains a grid line at all.
- The chat-template prompt format itself is not without merit (it does
  suppress the commentary-tail pattern specifically), but adopting it
  for production would also require deciding the TTT loss-masking
  question `chat_prompt_builder.py`/`_TextDataset` leaves open
  (currently full-sequence loss with only padding masked, not the
  system/user turns), a separate, larger decision not evaluated here.
- Confirms the chat-template diagnostic script and WSL2 invocation
  pattern (`wsl.exe -e bash -lc 'cd ... && source .venv312/bin/activate
  && PYTHONPATH=... python -m ...'`) work correctly end to end on real
  GPU hardware, reusable for any future diagnostic in this family.

## Alternatives considered

- **Treat the absence of a commentary tail as sufficient evidence the
  chat template resolves ADR 0053:** rejected; the aggregate table and
  raw text both show first-attempt parsing did not improve, and a new
  failure mode (full reasoning takeover) is at least as disruptive to
  correctness as the tail it replaces.
- **Extend this diagnostic with more tasks or attempts before
  concluding:** rejected for now; the patterns recur consistently
  across every held-out pair and across both tasks in the two chat
  files that had at least one parseable attempt, matching the standing
  1-2 task scope for this diagnostic tier; a broader sample belongs to
  a future tier, not this one.
- **Immediately design a decode-level mitigation in this same ADR:**
  rejected; per Golden Rule 1, a new mitigation lever is a separate
  decision requiring its own ADR before implementation, and the
  standing instruction only asks this ADR to confirm the cause is not
  prompt-resolvable, not to design the fallback.

## References

- [ADR 0010 - Raw generation inspection](0010-raw-generation-inspection.md)
- [ADR 0028 - Timing anomaly and task complexity investigation](0028-timing-anomaly-and-task-complexity-investigation.md)
- [ADR 0029 - Decoding mitigations for repetition and hallucination](0029-decoding-mitigations-repetition-hallucination.md)
- [ADR 0032 - Per-attempt conditional no_repeat_ngram_size mitigation](0032-per-attempt-conditional-ngram-mitigation.md)
- [ADR 0051 - Revert base model to Qwen3-4B-Instruct-2507, accepted-risk decision](0051-reversao-para-qwen3-risco-aceito.md)
- [ADR 0053 - Qwen3-4B-Instruct-2507 generation smoke test](0053-qwen3-instruct-generation-smoke.md)
