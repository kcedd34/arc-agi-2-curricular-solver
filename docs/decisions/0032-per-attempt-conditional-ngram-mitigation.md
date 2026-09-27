# 0032 - Per-attempt conditional no_repeat_ngram_size mitigation

## Status

Informative. Implements the refinement ADR 0031 named as an open next
step and re-tests it on the same 8-task sanity sample. This is the
closing round of the decode-mitigation investigation line that started
at ADR 0028: the production decision across all now-compared decode
strategies is still open and left to a joint call, not decided here.

## Context

ADR 0031 found a real adverse case in its task-conditional escalation
policy: each pair's first generation attempt always used plain baseline
decoding, and only if that one attempt showed ADR 0028's degenerate
pattern did the pair's remaining attempts escalate to
`no_repeat_ngram_size=3`. When a pair's first attempt was an
unrepresentative false negative, the pair never escalated and burned its
entire 6-attempt budget under slow, unmitigated decoding with nothing
recovered. This was the direct cause of `0934a4d8` coming out 24% slower
than plain baseline in that run (one of its 4 train pairs, pair 3, hit
this exact case). ADR 0031 named checking every attempt, not only the
first, as the concrete fix, but did not implement it.

## Method

New, isolated modules, same pattern as ADR 0031 and prior mitigation
work: the previous ADR 0031 code (`conditional_generation_diagnostics.py`,
`conditional_mitigation_pair_diagnostics.py`,
`run_conditional_mitigation_smoke.py`) is left untouched, and a parallel
set of files implements the refined policy.

- `src/solvers/neural/conditional_mitigation.py` (`shows_degenerate_pattern()`,
  `build_escalated_config()`): reused unchanged. Already generic enough,
  no change needed.
- `src/evaluation/per_attempt_conditional_generation_diagnostics.py`:
  `generate_with_per_attempt_conditional_counts()`, the only functional
  change versus ADR 0031. Every attempt's own completion is checked for
  the degenerate pattern, not only the first. Escalation triggers as
  soon as any attempt so far shows it, and is one-way: once triggered
  for a pair, later attempts never fall back to baseline, and an
  already-escalated pair is never re-checked. Generic over an injected
  per-attempt completion function, host-testable without a model/GPU.
- `src/evaluation/per_attempt_conditional_mitigation_pair_diagnostics.py`:
  per-task/per-pair GPU orchestration, close mirror of ADR 0031's
  version with the generation call swapped and a new
  `escalated_at_attempt` field per row.
- `src/evaluation/run_per_attempt_conditional_mitigation_smoke.py`: runs
  the refined policy once on the full 8-task sanity sample. `baseline`,
  `ngram_only`, and ADR 0031's first-attempt-only `conditional` are all
  reused unchanged, already persisted/logged.

7 new host tests
(`tests/test_per_attempt_conditional_generation_diagnostics.py`),
including a dedicated regression test for ADR 0031's adverse scenario
(`test_recovers_when_first_attempt_is_a_false_negative`), full suite
157/157 passing on both host Python and the WSL GPU venv.

## Results

### 1. Does `0934a4d8` stop being slower than baseline?

**No, and it got worse.** Per-pair comparison, ADR 0031's first-attempt-only
run versus this per-attempt run:

| Pair | ADR 0031 (attempt 0 only) | This ADR (every attempt) |
|---|---|---|
| train 0 | 4 attempts, escalated at attempt 0 | 4 attempts, escalated at attempt 2 |
| train 1 | 4 attempts, escalated at attempt 0 | 4 attempts, escalated at attempt 0 |
| train 2 | 4 attempts, escalated at attempt 0 | 4 attempts, escalated at attempt 0 |
| train 3 (the adverse case) | 6 attempts, kept 0, **never escalated** | 6 attempts, kept 1, escalated at attempt 1 |
| test 0 | 2 attempts, no escalation needed | 4 attempts, escalated at attempt 0 |
| **Total seconds** | **386.64** | **415.17** |

TTT time is unchanged between the two runs (81.76s vs 81.70s), so the
entire difference is in generation. Total time went **up**, from 24%
slower than plain `baseline` (312.50s) to 33% slower.

Train pair 3, the exact adverse case this refinement targets, **did
recover**: instead of running all 6 attempts under baseline with nothing
kept, it escalated after attempt 1 and kept 1 prediction. That part of
the fix works as designed.

But two other pairs moved the wrong way in this particular run,
independent of the refinement's logic:

- **Train pair 0** needed 3 baseline attempts before escalating this run
  (attempt 2), versus 1 baseline attempt in the ADR 0031 run (escalated
  at attempt 0). Its own attempt 0 was a non-degenerate false negative
  this run, which is exactly the scenario the per-attempt check is
  designed to survive, but surviving it here still means running more
  slow baseline attempts before recovering, not fewer.
- **Test pair 0** needed 4 attempts with escalation this run, versus 2
  clean attempts (no pattern, no escalation) in the ADR 0031 run.

Both of these are pairs that were not the design target (train pair 3
was); their completions differ between the two runs purely because
TTT/LoRA initialization and sampling are stochastic, the same caveat
ADR 0031 recorded explicitly. The refinement did what it was built to
do for the one pair it targeted, but in this specific run, sampling
variance elsewhere in the same task outweighed that gain.

### 2. Does `13e47133` keep or improve the 64% cut?

**Improves slightly.** Total time 497.12s versus `baseline`'s 1459.41s,
a 65.9% cut, versus ADR 0031's 64.0% cut (525.23s). All 5 pairs' first
attempts showed the pattern again this run (escalated at attempt 0
throughout), so this task's behavior is close to identical to ADR
0031's run; the small improvement is within the range of run-to-run
noise, not a structural change (per-pair attempt counts stayed the same
or nearly the same: 3/3/3/4/6 versus ADR 0031's 2/4/3/4/6).

### 3. Do the other 6 tasks remain regression-free?

**Yes.** Held-out per-cell accuracy on the 7 measurable test pairs:

| Task | `baseline` | ADR 0031 `conditional` | This ADR `conditional_per_attempt` |
|---|---|---|---|
| `135a2760` | 0.77 | 0.77 | 0.77 |
| `142ca369` | 0.45, 0.82 | 0.45, 0.81 | 0.45, 0.84 |
| `16b78196` | 0.89 | 0.89 | 0.90 |
| `16de56c4` | 0.59, 0.73 | 0.59, 0.73 | 0.59, 0.73 |
| `1818057f` | 0.90 | 0.89 | 0.89 |
| Mean (7 pairs) | 0.736 | 0.733 | **0.739** |

Mean held-out accuracy matches `baseline` within noise (delta +0.003),
same conclusion as ADR 0031. The more responsive checking does not
reintroduce ADR 0030's global regression (mean 0.583).

### 4. Does a new, more responsive borderline case appear?

**Yes, one, and it behaves as intended.** `16b78196` train pairs 0 and 1
both escalate under this policy (attempt 1 and attempt 0 respectively),
whereas under ADR 0031 they never escalated: their flagged attempt
existed but was never attempt 0, exactly the ADR 0031 Result 3 "benign
borderline" case (an isolated repetitive attempt without escalation).
Escalating on these pairs did not measurably harm the task: held-out
`16b78196` test pair 0 accuracy is 0.90, matching (fractionally
exceeding) `baseline`'s 0.89. No other pair among the 6 unaffected
tasks changed its escalation status versus ADR 0031's run.

## Hypothesis check

The refinement's goal was to make `0934a4d8` stop being slower than
`baseline` by letting a false-negative first attempt recover on a later
attempt, while keeping `13e47133`'s timing win and the other 6 tasks'
accuracy intact.

**Confirmed at the mechanism level, not at the task level.** The exact
adverse pair ADR 0031 flagged (`0934a4d8` train pair 3) did recover
exactly as designed: fewer wasted baseline attempts (2 instead of 6),
a kept prediction where before there was none. But `0934a4d8`'s total
task time still did not improve, because two other pairs in the same
task drew less favorable stochastic outcomes in this run than they did
in ADR 0031's run. Criteria 2, 3, and 4 are all confirmed as expected:
`13e47133` keeps and marginally improves its cut, the other 6 tasks stay
regression-free, and the more responsive checking does surface one new
escalation case, which is harmless.

## Consequences

- This closes the decode-mitigation investigation line that began at
  ADR 0028. Per the explicit scope for this round, no further
  refinement pass is planned before a production decision, even though
  `0934a4d8`'s result is not the clean win the refinement targeted.
- Four decode strategies for the 2 target tasks are now compared on this
  same 8-task sample: `baseline`, `ngram_only` (global, ADR 0030),
  `conditional` (first-attempt-only, ADR 0031), and
  `conditional_per_attempt` (this ADR). The production choice among
  them, and whether `0934a4d8`'s timing behavior is acceptable as-is,
  weighed against `13e47133`'s larger and more consistent win, and
  against the 6 unaffected tasks staying flat under every conditional
  variant, is left to a joint decision, not made here.
- The stochasticity caveat from ADR 0027/0029/0030/0031 is now directly
  illustrated, not just asserted: the same task, same policy design,
  same sanity sample, produced a worse total-time outcome on a second
  run because of per-pair sampling variance, not because the policy
  logic regressed. A single sanity-tier run is not sufficient to settle
  `0934a4d8`'s timing behavior either way; only a `validation`-tier run
  with multiple seeds could, per Golden Rule 7.
- Detection cost remains negligible: a pair that does not escalate runs
  the identical attempt sequence as `baseline`, unchanged from ADR 0031.

## Alternatives considered

- Running `0934a4d8` multiple times to average out stochastic variance
  before concluding anything about its timing behavior: not done here,
  since the user's explicit instruction was for this to be the closing
  round of this investigation line regardless of outcome; recorded as
  the natural extension a `validation`-tier run would provide.
- Escalating for the rest of the task once any pair shows the pattern,
  rather than per-pair: still not implemented, same reasoning as ADR
  0031 (keeps the blast radius of a false positive to one pair; Result
  3 shows the current per-pair scope already causes no harm when it
  escalates a pair that did not strictly need it).
- Reverting to ADR 0031's first-attempt-only policy given this run's
  worse `0934a4d8` outcome: not decided here, left to the joint
  production decision, since this run's data also shows the per-attempt
  policy is not worse on any other measured axis and does correctly fix
  the mechanism ADR 0031 flagged as broken.
