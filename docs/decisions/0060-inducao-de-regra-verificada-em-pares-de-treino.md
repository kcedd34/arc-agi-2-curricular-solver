# 0060 - Rule induction verified against train pairs (induce-verify-apply)

Status: Implemented and smoke-tested (2026-09-19). All 7 modules
(`program_prompt_builder.py`, `program_extraction.py`,
`program_sandbox_runner.py`, `program_sandbox.py`,
`program_verification.py`, `program_induction.py`,
`program_generation.py`) are built and unit-tested. The pre-registered
smoke test on `007bbfb7` ran for real on GPU hardware and returned this
ADR's own **Abandon** verdict (0 verified programs across 6 sampled
completions), see "Real smoke test result" below. Per Golden Rule 7 a
smoke-tier result never backs a policy decision alone; whether to retry
with a different `k`/temperature/prompt design or treat this line as
closed is an open joint call, not decided by this update.

## Context

Three real leaderboard submissions, all `publicScore 0.00` (refs
56256382, 56314323, 56360554). About 15 neural levers across ADR
0009-0039 and six symbolic primitive families across ADR 0040-0046 never
moved held-out `exact_match` off `0.0000`. ADR 0034's real signature:
mean per-cell accuracy `0.7716` (ADR 0059 measured `0.8291`/`0.9269`),
`exact_match_rate_test` `0.0000`, and training-pair-only matches.

Two facts explain that signature, and only one of them was already
documented.

**Known:** `exact_match` is all-or-nothing over every cell. A 9x9 output
needs 81/81 correct. A model at 90% per-cell accuracy scores exactly 0.
Partial credit is never rewarded, so every lever that improved per-cell
accuracy improved a metric the competition does not score.

**Not previously documented, found by code inspection for this ADR:** the
inference prompt contains **no examples at all**.
`build_inference_prompt` (`src/solvers/neural/prompt_builder.py:26`) is:

```
Input:
<test grid>
Output:
```

The task's train pairs reach the model only as LoRA weight updates during
TTT. At generation time the model is asked to transform a grid without
being shown a single instance of what the transformation is. It cannot
infer a rule from examples because the examples are not in its context;
it can only reproduce an approximate mapping absorbed into weights. High
per-cell accuracy with zero exact matches is the exact expected output of
that setup.

This is the gap between memorization and rule abstraction, located in our
own code rather than asserted abstractly.

## Decision (proposed)

Change **what the model emits**. Today it emits the answer grid (81+ cells,
all of which must be right, with no way to check them). Instead it emits
the **rule**, as a short Python function, and a free deterministic
verifier decides whether that rule is correct before it is ever applied
to the test input.

Three stages per task:

1. **Induce.** Prompt the model with all of the task's train pairs
   in context (the thing it currently never sees) and have it complete a
   `def transform(g):` body. Sample `k` candidates.
2. **Verify.** Run each candidate against every train pair. Keep only
   candidates that reproduce **100%** of them. This is ADR 0038's
   existing ambiguity bar, applied to model-generated programs instead of
   hand-written primitives. Costs no GPU and is exact.
3. **Apply.** Run a surviving program on the test input. If more than one
   survivor disagrees on the test output, the task is ambiguous: prefer
   the shortest program, and otherwise fall back to the existing symbolic
   /ADR 0011 chain, unchanged.

### Why this answers each recorded failure

| Recorded failure | What changes |
| --- | --- |
| Model must get 81/81 cells right (ADR 0034) | It must get one short rule right; the grid is then produced by exact execution |
| No way to tell a good prediction from a bad one (ADR 0009/0017, self-consistency never passes) | A wrong program is rejected with certainty by train-pair verification |
| Hand-written primitive catalogue covers 0/40 tasks twice (ADR 0042-0046) | The primitive is written per task by the model, not enumerated in advance |
| Per-cell gains never convert to score (ADR 0027/0039/0059) | Partial credit stops being the signal; the signal becomes binary train-pair reproduction |
| Prompt-format change already refuted (ADR 0054) | This is not a chat-template change. Format stays raw-completion on `Qwen/Qwen3-4B-Base`. What changes is the emitted unit and the verifier, not the wrapper |

The two dead lines become one loop: the neural side proposes primitives
(fixing the symbolic side's coverage problem), the symbolic side verifies
them (fixing the neural side's no-ground-truth problem).

### The prompt

Raw completion, not a chat template, deliberately ending mid-definition so
a Base model continues it as code rather than as instruction-following.
Grids are serialized with the existing `grid_to_text` (digit-string rows)
rather than nested Python lists, because nested lists cost roughly 3x the
tokens and `max_seq_length` is currently 2048.

```
# ARC-AGI-2 task. Each grid is a list of rows; each row is a string of
# digits 0-9, one digit per cell. The same rule maps every example input
# to its example output.

examples = [
    ("660\n600\n066",
     "660660000\n600600000\n066066000\n660000000\n600000000\n066000000\n000660660\n000600600\n000066066"),
    ("404\n000\n040",
     "404000404\n000000000\n040000040\n000000000\n000000000\n000000000\n000404000\n000000000\n000040000"),
    ("000\n002\n202",
     "000000000\n000000000\n000000000\n000000000\n000000002\n000000202\n000000000\n002000002\n202000202"),
]

# transform(g) takes the input grid as a list of digit-string rows and
# returns the output grid in the same form. It reproduces every example
# above exactly.
def transform(g):
```

Everything before `def transform(g):` is built mechanically from the
task's own train pairs. Nothing is hand-written per task.

### Blockers in our own code, checked, not assumed

Four things would silently discard this path's output if it were wired in
as-is:

1. **`has_topic_drift` rejects exactly what we want.**
   `src/evaluation/failure_mode_diagnostics.py:43` returns `True` for any
   completion containing `def `, `import `, or ` ``` `, or any line with
   4+ alphabetic words. It feeds `shows_degenerate_pattern`, and
   `generation.py:100` refuses to keep any completion that matches it
   (ADR 0056). A generated program is *by construction* flagged
   degenerate and thrown away. The program path needs its own detector
   set; the grid path's detectors stay untouched.
2. **`text_to_grid` cannot parse a program.**
   `grid_serialization.py:21` accepts only pure-digit rectangular lines.
   A separate extractor is needed for the completion, and the grid parser
   is then applied to the program's *return value*, not to the text.
3. **Executing model-written Python needs a sandbox.** Restricted
   builtins, no imports, no filesystem or network access, hard timeout,
   separate process. Golden Rule 4 is unaffected (the proposer is the
   local model, no API call), but arbitrary generated code is not.
4. **`max_seq_length = 2048` is probably too small.** Three 30x30 pairs in
   digit-string form are roughly 1800 tokens before the completion starts.
   Raising it has a real VRAM cost on the 8GB local GPU and must be
   measured, not assumed. Capping the number of in-context pairs is the
   cheaper alternative.

TTT does not disappear, but its target changes: instead of training on
`grid -> grid`, the natural corpus is `examples -> program`, which the
1000 public training tasks could supply. That is a second phase and is
not part of this proposal.

### Cheapest first test

`007bbfb7` (smoke tier, Golden Rule 7), this project's own original
smoke-test task. Its rule is about six lines of Python: each non-zero cell
of an `n x n` input becomes a full copy of the input in the corresponding
`n x n` block of an `n^2 x n^2` output, each zero cell becomes an empty
block. It has 5 train pairs and a known test output.

The question this smoke test answers, for a few minutes of GPU time: can
`Qwen/Qwen3-4B-Base` emit at least one train-pair-verified program for a
task whose rule is genuinely short? If it cannot, on the easiest possible
case, this whole line dies cheaply and nothing was built.

### Pre-registered criteria (same discipline as ADR 0057)

- **Proceed** if the smoke test produces at least one program that
  reproduces 5/5 train pairs. Whether it also gets the test pair right is
  secondary at this tier.
- **Abandon** if zero verified programs appear across `k` samples on
  `007bbfb7`.
- **Policy decisions still require validation tier** (30-50 tasks, Golden
  Rule 7). A smoke result never backs one on its own.
- The honest headline metric for this line is **verified-program coverage**
  (how many tasks produce at least one program passing 100% of their own
  train pairs), because that is measurable without ground truth and is
  the only quantity that can convert into `exact_match`.

### Real smoke test result (2026-09-19)

Ran `python -m src.evaluation.run_program_induction_smoke` for real on
WSL2 GPU hardware (`.venv312`, Unsloth 2026.9.2, `Qwen/Qwen3-4B-Base`,
Transformers 5.5.0, Torch 2.10.0+cu128, RTX 4060 Ti). Task loaded
correctly (`007bbfb7`, 5 train pairs, 1 test pair), model loaded with no
OOM, all `k=6` completions were sampled with no circuit-breaker abort.

Result: **0/6 completions verified against the 5 train pairs**, 0
ambiguous. None of the 6 raw completions implemented the real block-tiling
rule. By completion: (0) hallucinated prose, no usable code; (1) a
real-but-wrong color-remapping rule, plus hallucinated trailing prose
about a fictitious second task; (2) nonsensical, references an undefined
`examples` variable and a fabricated `test_transform()`; (3) unpacks `g`
as exactly 3 rows (`(a, b, c) = g`), not general, wrong logic; (4) a
border/interior classifier, unrelated to the real rule; (5) a simple
nonzero-to-`1` binarization, plus invalid Python-2-style print statements
as trailing hallucinated boilerplate. All 6 completions are either
unrelated transforms or non-code, never a working block-tiling
implementation.

This is exactly this ADR's own pre-registered **Abandon** criterion
(zero verified programs across `k` samples). Per Golden Rule 7 this
smoke-tier result is enough to conclude the smoke test itself negatively,
but does not by itself decide whether the whole induce-verify-apply line
is closed, needs a larger `k`/different temperature, or needs a
different prompt design (e.g. one worked example program shown before
the task's own, few-shot style) as a cheaper next lever than abandoning
outright. That decision is left to the user, not resolved here.

### Corrected retry, real k=96 result (2026-09-19)

Per the open question the first result left, the cheaper next lever was
tried before abandoning the line: a worked few-shot example prepended to
the prompt, `k` raised from 6 to 96, and grid serialization switched from
escaped-newline strings to a `repr()`-based `List[str]` literal
(`program_prompt_builder.py`, `DEFAULT_NUM_CANDIDATES = 96` in
`program_generation.py`). All three changes were implemented and
unit-tested before any GPU run.

**A real bug was found and fixed first.** The first k=96 attempt reused
`run_program_induction_smoke.py`'s hardcoded
`NEURAL_TASK_CEILING_SECONDS=400.0` circuit breaker (ADR 0049) unmodified.
That ceiling is sized for one task's production TTT+generation cycle; this
diagnostic has no TTT, only k serial samples, so at k=96 it aborted after
about 14/96 completions, well before finishing. Fixed by adding a
`--ceiling-seconds` CLI argument (default: the old 400s constant, for
backward compatibility), and the run was relaunched with
`--ceiling-seconds 4500 --num-candidates 96`.

**Real result:** all 96 completions were sampled with zero circuit-breaker
aborts (confirmed by grep: 96 `--- completion N ---` markers, zero
`abort`/`circuit breaker`/`exceeded` matches anywhere in the log).

```
Verified programs: 0
Ambiguous: False
Verdict: ABANDON (zero verified programs reproduced all 5 train pairs)
```

**0/96 completions verified against the 5 train pairs.** Manual
inspection of a sample of completions shows the worked example changed
the *shape* of the failures without producing a correct one. Several
completions (e.g. completions 0, 1, 4, 5) now attempt something
structurally in the neighborhood of the real rule - row-wise or
block-wise repetition/tiling logic - rather than being unrelated
transforms outright, a plausible effect of the worked example nudging the
model toward a tiling-shaped continuation. None get the indexing or block
placement right. Other completions remain entirely unrelated to the real
rule (e.g. completion 7: elementwise `cell + 1`; completion 8: per-row
diagonal extraction). A recurring, distinct failure mode not present at
k=6: 15/96 completions (confirmed by grep on
`"# Now a new ARC-AGI-2 task"`) hallucinate an entire second, fictitious
ARC task (fake `examples = [...]`, sometimes a fake harder task, sometimes
fake meta-commentary about "submission validity" or a `test_transform()`
harness) instead of terminating cleanly after one `transform` definition.
This is a genuinely complete, non-aborted, materially larger sample than
either the original k=6 attempt or the first (aborted) k=96 attempt, and
it still lands on the same **Abandon** verdict.

Per Golden Rule 7, this remains a `smoke`-tier result (single task,
`007bbfb7`) and cannot by itself justify closing or continuing the whole
induce-verify-apply line as a matter of policy. It is materially stronger
evidence than either prior attempt: the corrected-retry design (worked
example + k=96 + `repr()` encoding) was tested to genuine completion, not
cut short, and did not produce a single verified program. Whether to
retry with a different base model (e.g.
`Qwen/Qwen3-4B-Instruct-2507`), a different prompt design, or to close
this line is an open joint call left to the user.

## Consequences

- Nothing is implemented by this ADR. No file under `src/` changes, no
  GPU run happens, no Kaggle action is taken.
- If accepted, the build is mostly new: a few-shot program-induction
  prompt builder, a completion-to-program extractor, a sandboxed runner,
  and a verifier. The verifier's semantics (100% of train pairs, more than
  one disagreeing survivor means ambiguous) are reused from ADR 0038, not
  reinvented.
- The existing grid-emission path is not removed or weakened. This would
  be a second candidate source feeding the same symbolic/ADR 0011 fallback
  chain.
- `docs/writeup/solution_writeup_draft.md` would need updating either way
  (Golden Rule 8): a negative result here is genuine Theory content for
  the Innovation Prize, the same as the ADR 0042-0046 nulls.
- Honest risk: a 4B base model writing correct Python for novel visual
  puzzles is a real stretch. The argument for trying it anyway is that
  Python is heavily represented in its pretraining while ARC grid text
  format is represented nowhere, and that verification makes a low hit
  rate still useful, because a 5% rate of verified programs is 5% of real
  exact matches against a structural 0%.

## Alternatives considered

- **Keep improving per-cell accuracy.** Rejected as the primary line: 15
  levers moved it and never moved the scored metric, which is exactly what
  an all-or-nothing metric predicts.
- **Emit the rule in natural language instead of code.** Rejected: natural
  language cannot be verified mechanically against the train pairs, which
  is the entire value of this proposal.
- **Scale cross-task pretraining to 400-600 tasks (ADR 0057/0059).**
  Not rejected, but deferred: ADR 0059's controlled reanalysis gives
  `+0.0387` per-cell with `exact_match` still `0.0000` in both arms, at a
  real cost of 18.91-126.31h. It improves the unscored metric.
- **Extend the hand-written primitive catalogue (ADR 0041 items 4/5).**
  Rejected by ADR 0046 on two independent 40-task samples; this proposal
  reaches the same goal without needing the catalogue to be complete.
- **Use a chat template or a larger instruct model.** Rejected: ADR
  0054 already refuted the chat-template path on this family, and ADR
  0055 moved deliberately to the Base variant.

## References

- [ADR 0034 - First validation-tier run of the consolidated config](0034-first-validation-consolidated-config.md)
- [ADR 0038 - Fixed output shape rule](0038-fixed-output-shape.md)
- [ADR 0040 - Priority pivot: symbolic solver becomes primary](0040-pivot-prioridade-solver-simbolico.md)
- [ADR 0046 - Second independent sample confirms the null pattern](0046-segunda-amostra-cobertura-simbolica.md)
- [ADR 0054 - Chat-template prompt format test](0054-formato-chat-template-qwen3.md)
- [ADR 0055 - Qwen3-4B-Base vs Instruct](0055-qwen3-base-vs-instruct.md)
- [ADR 0056 - Parser leniency fix and 4-failure-mode mitigation](0056-mitigacao-4-modos-qwen3-base.md)
- [ADR 0059 - Intermediate-scale cross-task pretraining pilot](0059-piloto-pretreino-qwen3-base.md)
