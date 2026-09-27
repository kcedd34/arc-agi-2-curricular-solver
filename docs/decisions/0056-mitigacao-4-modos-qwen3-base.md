# 0056 - Fixing parser leniency and adapting mitigations to Qwen3-4B-Base's four failure modes

Status: Informative

## Context

[ADR 0055](0055-qwen3-base-vs-instruct.md) confirmed a measurement problem
that had already surfaced in [ADR 0053](0053-qwen3-instruct-generation-smoke.md)
and gone uncorrected: the parser counts `parsed=2, kept=2` for completions
whose content is degenerate repetition (e.g. an all-zero grid repeated many
times), not a genuinely valid prediction candidate. This risked inflating
"parsed"/"kept" metrics across several prior ADRs without that being
noticed at the time.

With that measurement corrected, this ADR adapts the already-validated
OLMo-2 mitigations ([ADR 0010](0010-raw-generation-inspection.md)'s EOS fix,
[ADR 0029](0029-decoding-mitigations-repetition-hallucination.md)-[0032](0032-per-attempt-conditional-ngram-mitigation.md)'s
conditional decoding mitigation) to Qwen3-4B-Base, now covering four known
failure modes instead of three, per the governing instruction that opened
this investigation.

## Step 1: parser-leniency fix (a measurement correction, not a generation fix)

### Root cause

The prior logic counted any completion that parsed into a rectangular grid
of consistent row width as `kept`, regardless of whether its content is
degenerate (all-zero, or dozens of identical rows) rather than a genuine
attempt at the task. A completion can be structurally parseable and
substantively worthless at the same time; the parser conflated the two.

### Fix applied

- `shows_degenerate_pattern` (`src/solvers/neural/conditional_mitigation.py`)
  is reused as the gate: any completion matching one of the textual
  detectors in `failure_mode_diagnostics.py` (hallucinated second example,
  degenerate line-level repetition, and the topic-drift detector added by
  this ADR) is excluded from `kept`, even when it technically parses.
- Applied across all three code paths that compute this count: the
  production path (`generation.py`'s `generate_grid_predictions`), the
  diagnostic path used by `run_generation_diagnostics.py`
  (`generation_diagnostics.py`'s `generate_with_counts`), and the per-attempt
  diagnostic module (`per_attempt_conditional_generation_diagnostics.py`'s
  `generate_with_per_attempt_conditional_counts`).
- An instrumentation gap was found and fixed in this session in
  `run_generation_diagnostics.py`: its `PairDiagnosticRow` dataclass did not
  repass the already-computed `num_parsed_but_degenerate` field into the
  persisted JSON row or the printed markdown table. Fixed by adding the
  field to the dataclass, threading it through `_diagnose_pairs`, and adding
  a "Parsed-but-degenerate" column to `_render_markdown`'s header and rows.

### Retroactive reprocessing of already-persisted data (no new GPU run)

Reprocessing the data already saved from ADR 0053/0054/0055 with the
corrected logic:

- ADR 0053: kept 8 -> 1
- ADR 0054: kept 4 -> 4 (unchanged)
- ADR 0055: kept 14 -> 11

**Caveat governing all three ADRs**: every "parsed"/"kept" number reported
in ADR 0053, 0054, and 0055 should be read with this reservation. Some
fraction of what those ADRs counted as "kept" was degenerate repetition
miscounted as a valid candidate; their own qualitative conclusions, which
relied on direct raw-text inspection rather than the aggregate count alone,
are not invalidated by this, but the numeric "kept" figures they quote are
inflated relative to the corrected definition.

### Mechanical confirmation: new smoke test with the corrected instrumentation

`python -m src.evaluation.run_generation_diagnostics evaluation 135a2760,136b0064`
was re-run with the corrected instrumentation, confirming that
`num_parsed_but_degenerate` appears correctly in both the printed table and
the persisted per-task JSON files.

| Task | Split | Pair | Attempts tried | Parsed | Parsed-but-degenerate | Kept | Exact match |
|---|---|---|---|---|---|---|---|
| 135a2760 | train | 0 | 2 | 2 | 0 | 2 | yes |
| 135a2760 | train | 1 | 4 | 3 | 0 | 2 | no |
| 135a2760 | test | 0 | 3 | 2 | 0 | 2 | no |
| 136b0064 | train | 0 | 3 | 3 | 1 | 2 | no |
| 136b0064 | train | 1 | 2 | 2 | 0 | 2 | no |
| 136b0064 | train | 2 | 2 | 2 | 0 | 2 | no |
| 136b0064 | test | 0 | 3 | 3 | 1 | 2 | no |

- `136b0064` train pair 0 and test pair 0 both show
  `num_parsed_but_degenerate=1`, confirming the mechanism excludes a
  parseable-but-degenerate completion from `kept` in a freshly generated
  run, not only retroactively against old data.
- `135a2760` train pair 1's gap (4 attempts, 3 parsed, 2 kept) is
  pre-existing deduplication (two attempts yielding an identical
  prediction), not degeneration, confirmed by its
  `num_parsed_but_degenerate=0`; this distinction matters, since deduplication
  and degeneration would otherwise look identical in a bare "parsed > kept"
  reading.

**Limitation: sampling stochasticity.** `do_sample=True` with per-attempt
incremental seeds does not guarantee identical completions across separate
executions of the same script (GPU kernel/RNG-state non-determinism). This
run's specific numbers differ from an earlier manual-inspection round
performed on the same two tasks during this investigation (raw files
preserved under
`outputs/raw_generations/evaluation/_adr0056_manual_inspection_round/`):
for example, `135a2760_test_0` shows no degeneration in this run, though the
manual round's `135a2760_test_0_0.txt` clearly showed topic drift. This new
run therefore serves as **mechanical confirmation that the corrected metric
computes and persists correctly**, not as an independent second
reproduction of every failure mode; the primary evidence for each failure
mode's presence on Qwen3-4B-Base is the manual-inspection round described
in Step 2.

## Step 2: adapting the mitigation to four failure modes

### Manual-inspection evidence (primary source for this step)

Twenty raw completions from an earlier real run on these same two tasks
were inspected manually and preserved for this ADR. Concrete findings per
failure mode:

1. **EOS / generation stopping.** ADR 0010's fix is confirmed still active:
   `ttt_trainer.py` appends `tokenizer.eos_token` to every training text
   (its `_append_eos` helper, lines 61-66), and `generation.py` passes
   `eos_token_id=tokenizer.eos_token_id` to `model.generate`. Across the 27
   completions inspected in this investigation (20 from the manual round
   plus 7 from this session's new run), no attempt exhausted the retry cap
   purely from failing to emit a stop token. **Not confirmed as a recurring
   blocker on Base in this sample**; the fix stays active as a safeguard
   and is not removed.

2. **Degenerate line-level repetition (ADR 0028).** **Confirmed recurring on
   Base.** `136b0064_train_0_1.txt`/`136b0064_train_1_1.txt` from the manual
   round: a plausible small grid start, then runaway all-zero-row repetition
   to the token cap. Reconfirmed mechanically in this session's new run
   (`136b0064` train pair 0 and test pair 0, both
   `num_parsed_but_degenerate=1`). Covered by `has_degenerate_repetition`
   (a run of at least 10 identical consecutive non-blank lines), reused
   unchanged from ADR 0028/0029.

3. **Hallucinated second "Input:" example.** **Not observed** in any of the
   27 completions inspected across both rounds in this session. The
   detector `has_hallucinated_second_example` (ADR 0028/0029) stays active
   and is not removed; this is understood as an Instruct-associated pattern
   (ADR 0053) not reproduced on Base in this sample, not as dead code to
   drop.

4. **Topic drift (new).** **Confirmed recurring on Base.**
   `135a2760_test_0_0.txt` from the manual round: a complete, well-formed
   29-row grid, followed by "Sure! Here is the Python code that inverts an
   8 x 8 matrix:" plus a Python function definition, cut off mid-token at
   the token cap. A new detector, `has_topic_drift`, was added to
   `failure_mode_diagnostics.py`: it returns true if the completion contains
   any of the code markers (` ``` `, `def `, `import `), or if any single
   line carries four or more alphabetic words (regex `[A-Za-z]+`). A
   genuine grid line is pure digits, so either signal already places that
   line outside the expected grid format.

### Mitigation adaptation

- `shows_degenerate_pattern` (`conditional_mitigation.py`) now checks all
  three textual detectors (`has_hallucinated_second_example`,
  `has_degenerate_repetition`, `has_topic_drift`), one more than the two it
  covered when first built for OLMo-2.
- ADR 0032's per-attempt conditional escalation policy is otherwise
  unmodified: a pair's first attempt always runs under baseline decoding,
  and any attempt (not only the first) matching `shows_degenerate_pattern`
  escalates the pair's remaining attempts to `no_repeat_ngram_size=3`
  (`build_escalated_config`), one-way, per-pair.
- Step 1's "exclude from kept" gate reuses the same three-detector check, so
  a completion that trips the new topic-drift detector is now also excluded
  from `kept`, not only from triggering escalation.
- No change to `repetition_penalty` (already found close to inert by ADR
  0030) or to the EOS fix (ADR 0010).

### Smoke test

Run on the same two tasks (`135a2760`, `136b0064`), same command as Step
1's re-run; results are the table shown in Step 1. That run's own numbers
reconfirm the degenerate-repetition detector firing correctly on
`136b0064`, but, per the stochasticity caveat above, do not independently
reproduce the topic-drift or hallucination patterns in this specific
execution; that evidence is carried by the manual-inspection round.

## Decision

- The Step 1 parser fix is adopted and applied uniformly across the
  production and diagnostic code paths. All "parsed"/"kept" numbers
  reported before this fix (ADR 0053/0054/0055, and any earlier ADR relying
  on the same code paths) are to be read with the stated caveat, not
  edited retroactively in those ADRs' own text.
- The Step 2 mitigation policy now checks four failure modes (EOS,
  degenerate repetition, hallucinated second example, topic drift). Of
  these, two are evidenced as actively occurring on Qwen3-4B-Base in this
  sample (degenerate repetition, topic drift), one remains an
  active-but-unconfirmed-as-a-blocker safeguard (EOS fix), and one remains
  an active-but-unreproduced-on-Base detector (hallucination).
- No existing mitigation (ADR 0010, ADR 0029-0032) is removed or weakened;
  `has_topic_drift` is purely additive to `shows_degenerate_pattern`.
- Per the governing instruction, this ADR does not advance to tier 3
  (8-task sanity run) and does not touch Kaggle in any way.

## Consequences

- Future ADRs reusing `run_generation_diagnostics.py`/
  `generation_diagnostics.py`/`per_attempt_conditional_generation_diagnostics.py`
  get a `kept` metric that already excludes degenerate-but-parseable
  completions, closing the specific gap ADR 0053/0055 both hit without
  noticing at the time.
- `conditional_mitigation.py`'s escalation policy now triggers on three
  detectors instead of two, which may in principle change which pairs
  escalate to `no_repeat_ngram_size=3`, and therefore which pairs inherit
  ADR 0030's documented held-out-accuracy regression risk associated with
  that parameter. This effect is not measured at `sanity`/`validation`
  scale in this ADR and remains an open question for a future run.
- The stochasticity of `do_sample=True` generation means a single smoke-tier
  re-run, including this ADR's own, should not be read as a full
  reproduction of every named failure mode; manual inspection of preserved
  raw text remains the more reliable evidence source at this tier,
  consistent with this project's own established practice (ADR 0053/0055)
  of never trusting aggregate counts alone.
- Whether to promote this adapted mitigation to `sanity`/`validation` tier,
  and whether the topic-drift detector's thresholds (a run of 10 identical
  lines, four or more alphabetic words per line) hold up at scale without
  false positives, remain open joint calls.

## Alternatives considered

- **Retroactively rewrite ADR 0053/0054/0055's own reported numbers**:
  rejected. Those ADRs are a historical record of what was measured and
  concluded at the time, and their own conclusions relied on direct
  raw-text inspection, not the aggregate "kept" count alone. Adding this
  ADR's reservation is more honest than silently editing prior documents.
- **Tighten `has_topic_drift`'s natural-language threshold below four words
  to catch shorter tangents**: rejected without stronger evidence; four
  words balances against false-positiving on a completion that includes a
  short label or comment without genuinely drifting off-topic. A stricter
  threshold is deferred to a future validation-tier false-positive check.
- **Re-run the smoke test repeatedly until every failure mode reproduces
  mechanically in a single execution**: rejected. Per Golden Rule 7,
  smoke-tier results (one to two tasks) never justify a policy decision on
  their own, and chasing one specific stochastic reproduction at this tier
  would misrepresent a single sample as more conclusive than it is. The
  manual-inspection round already on file is sufficient evidence for this
  tier's purpose, confirming the failure modes exist and are covered by the
  updated detectors.

## References

- [ADR 0010 - Raw generation inspection](0010-raw-generation-inspection.md)
- [ADR 0028 - Timing anomaly and task complexity investigation](0028-timing-anomaly-and-task-complexity-investigation.md)
- [ADR 0029 - Decoding mitigations for repetition and hallucination](0029-decoding-mitigations-repetition-hallucination.md)
- [ADR 0030 - Splitting the repetition-mitigation parameters](0030-splitting-repetition-mitigation-parameters.md)
- [ADR 0031 - Conditional no_repeat_ngram_size mitigation](0031-conditional-ngram-mitigation.md)
- [ADR 0032 - Per-attempt conditional no_repeat_ngram_size mitigation](0032-per-attempt-conditional-ngram-mitigation.md)
- [ADR 0053 - Qwen3-4B-Instruct-2507 generation smoke test](0053-qwen3-instruct-generation-smoke.md)
- [ADR 0054 - Chat-template prompt format test for Qwen3-Instruct's new failure modes](0054-formato-chat-template-qwen3.md)
- [ADR 0055 - Qwen3-4B-Base vs Instruct](0055-qwen3-base-vs-instruct.md)
