# 0010 - Raw generation inspection

Status: Accepted

## Context

ADR 0009 found that neural generation never produces a single parseable
grid for 5/8 sample tasks (79% of all pairs) and produces well-formed but
always-wrong grids for the other 3/8, without explaining why parsing
fails so often. The leading hypothesis at the time was that larger
expected output grids get truncated by the fixed `max_new_tokens=1024`
budget before the model finishes writing them out.

This ADR inspects the raw, pre-parsing completion text captured by
`src/evaluation/run_generation_diagnostics.py` (evaluation split, 8
tasks, 6 sampling attempts per pair, raw text persisted under
`outputs/raw_generations/evaluation/`) to test that hypothesis directly.

## Finding

The truncation hypothesis, as originally framed (large expected grids
run out of token budget), is **not** the primary driver. Inspecting raw
completions across tasks with very different expected output sizes
shows the same failure mode regardless of size:

| Task / pair | Expected output dims (cells) | Observed raw completion |
|---|---|---|
| `136b0064` train 0 (15x7=105, small/medium boundary) | 15 wide, 7 tall | 15-char-wide rows, runs 64+ rows, motif repeats once then degenerates to all-zero rows, cut mid-stream |
| `136b0064` train 1 (7x7=49, small) | 7 wide, 7 tall | 9 or 15-char-wide rows (neither matches expected width), runs 64-103 rows before the token budget cuts it off |
| `13e47133` train 0 (20x20=400, medium/large boundary) | 20 wide, 20 tall | 20-char-wide rows (width matches input), a plausible pattern for ~16 rows, then repeats one row indefinitely to row 49, cut mid-row |
| `0934a4d8` test 0 (9x3=27, small) | 9 wide, 3 tall | 31-char-wide rows of a single repeated digit, runs 33+ rows, cut mid-row |
| `16de56c4` train 2 (dims not the point here) | - | 15-char-wide rows, one digit changes once then repeats a single row 50+ times, cut cleanly at a trailing blank line |

Every sample inspected, independent of the task's true expected size,
generates far more rows than any plausible correct grid and only stops
because `max_new_tokens` (1024) is exhausted, not because the model
chose to stop. Whether that cutoff lands on a clean row boundary
(happens to "parse" as a valid, if wrong-content, grid, e.g.
`136b0064` train 1 attempt 1) or mid-row (fails to parse at all, e.g.
`0934a4d8` test 0 attempt 0) is incidental to where in its own
repeating pattern the model happened to be at token 1024, not related
to whether the true output was "too big to fit."

**Root cause identified:** `src/solvers/neural/prompt_builder.py`'s
`format_pair_as_text` builds each TTT training example as
`"Input:\n<grid>\nOutput:\n<grid>"` with no terminator after the output
grid, and `src/solvers/neural/ttt_trainer.py`'s `_TextDataset` tokenized
that text as-is, with no EOS token appended. The model is therefore
never shown, during training, where a correct output is supposed to
end. At generation time (`src/solvers/neural/generation.py`, plain
`model.generate(..., do_sample=True)` with no `eos_token_id` passed
before this fix), there is no learned signal to stop, so sampling
degenerates into repeating the last row it generated until the hard
token cap ends it, regardless of the task's true output size.

This also explains a fact the original size-truncation hypothesis could
not: small-grid tasks (e.g. `136b0064` train 1, 7x7 expected) fail the
same way as the largest sampled task (`13e47133`, 20x20 expected) - if
token budget vs. grid size were the driver, small grids should have
succeeded far more often, and they do not.

## Decision

Apply the fix this finding points to, since it is narrow, low-risk, and
standard practice for causal-LM fine-tuning (append an explicit stop
token after the target text so the model learns to predict it):

1. `src/solvers/neural/ttt_trainer.py`: new `_texts_with_eos(texts,
   tokenizer)` appends `tokenizer.eos_token` to every training example
   before tokenization, called from `train_on_task`.
2. `src/solvers/neural/generation.py`: `_generate_completion` now passes
   `eos_token_id=tokenizer.eos_token_id` explicitly to `model.generate`,
   so sampling honors an emitted EOS instead of relying only on
   whatever `model.generation_config` happens to carry through
   Unsloth/PEFT wrapping.

`src/solvers/neural/prompt_builder.py` is intentionally left unchanged:
it stays tokenizer-agnostic pure text construction (one responsibility),
the EOS token is a tokenizer-level concept and belongs in the layer that
already tokenizes.

Per the standing instruction from the OSAID-compliance session (apply
the parsing fix now that it is both concluded and clear, before running
a new evaluation with OLMo-2-1124-7B), this fix is applied, not just
proposed. It has **not** been validated against real generation output
yet, that requires GPU execution, which is exactly what the deferred
smoke test and future evaluation runs are for. `pytest tests/` passes
mechanically (57/57, including two new pure-logic tests for
`_texts_with_eos` in `tests/test_ttt_trainer.py`), but this is not an
accuracy or generation-quality confirmation.

## Consequences

- A new full evaluation run with OLMo-2-1124-7B can now proceed once the
  user confirms both changes (compliant model, ADR 0014, and this
  parsing fix) are ready to run together, per that earlier instruction.
  Not run as part of this ADR.
- If this fix does not fully resolve the degenerate-repetition behavior
  (e.g. if the base, non-instruction-tuned model still struggles to
  learn a stop point from only a handful of TTT steps), the next lever
  to investigate would be training data structure (e.g. an explicit
  separator between concatenated examples) or generation-side
  mitigations (repetition penalty, a max-row stopping criterion tied to
  the expected output height when known). Not decided or implemented
  here, flagged for a future diagnostic if the fix proves insufficient.
- This finding also matters for the upcoming GPU memory smoke test: the
  runaway-generation behavior observed here means, before this fix,
  TTT-phase memory was likely never the bottleneck the smoke test is
  probing, generation-phase memory (long sequences generated during
  self-consistency sampling) could have been. Worth keeping in mind when
  reading that result.

## Alternatives considered

- **Leave the size-truncation hypothesis as the working theory and move
  straight to widening `max_new_tokens`:** rejected, the evidence shows
  this would not fix small-grid tasks and would only make every
  degenerate generation longer (worse latency, no accuracy gain).
- **Add stopping criteria based on repeated-row detection instead of an
  EOS token:** rejected as a first fix, more complex than teaching the
  model a normal stop token, kept as a fallback idea if the EOS fix
  proves insufficient.

## References

- [ADR 0008 - Error diagnosis, first round](0008-error-diagnosis-first-round.md)
- [ADR 0009 - Empty-candidate diagnosis](0009-empty-candidate-diagnosis.md)
- [ADR 0014 - OSAID-compliant base model](0014-osaid-compliant-base-model.md)
