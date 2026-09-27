# 0031 - Conditional no_repeat_ngram_size mitigation

## Status

Informative. Implements and sanity-tests the task-conditional escalation
policy ADR 0030 named as an untested open alternative. Confirms one of the
two goals cleanly, finds the other only partially met, and surfaces a
concrete design weakness. Does not propose a production default.

## Context

ADR 0030 confirmed `no_repeat_ngram_size=3` alone drives essentially all of
both the fix (eliminates `13e47133`'s degenerate repetition, cuts
`0934a4d8`'s hallucination substantially, large generation-time cuts on
both) and the harm (held-out per-cell accuracy on the 6 unaffected sanity
tasks regresses from a mean of 0.736 to 0.583, about -21% relative) when
applied globally to every attempt of every pair. Since the 2 target tasks'
gain is purely a timing win (their content stays wrong either way, ADR
0030 Result 3) and the loss lands exactly on the 6 tasks where the model is
actually improving (the same tasks color augmentation helps, ADR 0027),
adopting the global mitigation is not worth it. This ADR implements and
tests the conditional alternative ADR 0030 left open instead of deciding
that tradeoff.

## Method

New, isolated modules, same pattern as prior mitigation modules:

- `src/solvers/neural/conditional_mitigation.py`: pure decision policy, no
  GPU dependency. `shows_degenerate_pattern()` reuses
  `failure_mode_diagnostics.has_hallucinated_second_example`/
  `has_degenerate_repetition` unchanged. `build_escalated_config()` applies
  only `no_repeat_ngram_size=3` (ADR 0030's `ngram_only` value;
  `repetition_penalty` is left out, ADR 0030 found it close to inert).
- `src/evaluation/conditional_generation_diagnostics.py`:
  `generate_with_conditional_counts()`, the per-pair attempt loop. Attempt
  0 always uses the baseline config. If it shows the degenerate pattern
  and `enable_conditional_escalation` is `True` (the on/off flag), every
  remaining attempt for that pair switches to the escalated config;
  otherwise every attempt stays on baseline. Same early-stop attempt
  budget as `generation_diagnostics.generate_with_counts`. Generic over an
  injected per-attempt completion function, so this control flow is
  host-testable without a model.
- `src/evaluation/conditional_mitigation_pair_diagnostics.py`: per-task/
  per-pair GPU orchestration, same shape-constrained reading as
  `mitigation_diagnostics.py`, adds an `escalated` field per row.
- `src/evaluation/run_conditional_mitigation_smoke.py`: runs the policy
  (`enable_conditional_escalation=True`) once on the full 8-task sanity
  sample. `baseline` and the fully-escalated `ngram_only` are not re-run,
  both already persisted/logged by ADR 0029/0030 on this same sample and
  reused unchanged for comparison, same practice ADR 0030 used for
  `baseline`/`repetition_only`/`stop_heuristic_only`/`both`.

11 new host tests (`tests/test_conditional_mitigation.py`,
`tests/test_conditional_generation_diagnostics.py`), full suite 150/150
passing.

## Results

### 1. Do the 2 target tasks still get the timing benefit, only when detected?

Per-pair escalation outcome and total generation time:

| Task | Pairs escalated | Total attempts | Total seconds (conditional) | `baseline` | `ngram_only` |
|---|---|---|---|---|---|
| `0934a4d8` | 3/5 | 20 | **386.64** | 312.50 | 105.24 |
| `13e47133` | 5/5 | 19 | **525.23** | 1459.41 | 111.72 |

`13e47133`: every pair's first attempt showed the pattern, so every pair
escalated, and total time drops 64% versus `baseline` (525s vs 1459s) - a
real, substantial win, though smaller than `ngram_only`'s 92% cut (112s),
since attempt 0 of every pair still has to run to completion under the
slow baseline config before the pattern can even be checked.

`0934a4d8`: 3 of 4 train pairs escalated and generated fast afterward, but
the 4th train pair's first attempt did not show the pattern, so it never
escalated - and that one pair then spent its entire 6-attempt budget under
slow `baseline` decoding, still failing (0 kept, 5/6 hallucinated). Total
time for this task came out **24% slower than plain `baseline`** (386.64s
vs 312.50s), not faster. See Result 3.

### 2. Are the other 6 tasks free of the regression?

Held-out test-pair per-cell accuracy, conditional vs. `baseline` (ADR 0027/
0029) vs. global `ngram_only` (ADR 0030):

| Task | `baseline` | `conditional` | `ngram_only` |
|---|---|---|---|
| `135a2760` | 0.77 | 0.77 | 0.54 |
| `142ca369` | 0.45, 0.82 | 0.45, 0.81 | 0.32, 0.69 |
| `16b78196` | 0.89 | 0.89 | 0.78 |
| `16de56c4` | 0.59, 0.73 | 0.59, 0.73 | 0.51, 0.68 |
| `1818057f` | 0.90 | 0.89 | 0.56 |
| Mean (7 pairs) | 0.736 | **0.733** | 0.583 |

**Confirmed.** Mean held-out accuracy on the 6 unaffected tasks lands at
0.733, matching `baseline`'s 0.736 within noise (delta -0.003), not
`ngram_only`'s regressed 0.583. Only one row among these 6 tasks'
11 measurable pairs escalated at all (`142ca369` test pair 0, see Result
3), and even there accuracy still matched `baseline` (0.45). The
regression ADR 0030 flagged is resolved by the conditional approach on
this sample.

### 3. Border-line pairs

Two distinct border-line patterns showed up, in opposite directions:

- **`0934a4d8` train pair 3 (the adverse case).** Attempt 0 did not show
  the degenerate pattern, so escalation never triggered, but the pair
  itself was one of the hardest in the sample: it ran the full 6-attempt
  cap, kept 0 predictions, and 5 of its 6 raw completions were flagged
  hallucinated. A single unrepresentative first attempt (a false negative)
  locks a pair into slow, unmitigated decoding for its entire remaining
  budget with no recovery mechanism. This is the direct cause of Result
  1's timing loss on `0934a4d8`, and it is a structural weakness of
  checking only attempt 0, not sample noise alone.
- **`16b78196` and `142ca369` test pair 0 (the benign case).** Several
  pairs across the unaffected tasks show 1-2 individual attempts flagged
  by the same pattern detectors, without ever escalating (because the
  flagged attempt was not attempt 0) or after escalating on just one pair
  (`142ca369` test 0). In every one of these cases the pair's final
  accuracy still matched its `baseline` value. An isolated, non-first
  degenerate attempt, or an isolated single-pair escalation, did not
  measurably harm outcomes in this sample.

### 4. Added cost of detection on tasks that do not need mitigation

By construction, a pair that never escalates runs the exact same sequence
of attempts, under the exact same config, as plain `baseline` decoding -
`generate_with_conditional_counts` never inserts an extra generation call,
it only inspects text already produced by the first attempt the loop would
have run anyway. Across the 6 unaffected tasks' 24 pairs, only 1 pair
escalated; the other 23 ran an identical control flow to `baseline`. This
is consistent with Result 2's accuracy match (0.733 vs. 0.736) and with
this ADR's design: detection itself costs a cheap in-process string check,
not a model call. This ADR does not include a matched-seed `baseline`
re-run of these 6 tasks' total generation seconds specifically (ADR 0029/
0030 only measured total seconds for the 2 target tasks, not these 6), so
exact per-second overhead is inferred from the identical control flow and
the unaffected accuracy, not independently timed; a future run could add
that direct measurement if the joint decision wants it.

## Hypothesis check

The user's expectation was: (1) the 2 target tasks keep the timing
benefit, only when the pattern is detected, and (2) the other 6 tasks are
free of the regression.

**(2) is confirmed cleanly.** **(1) is only partially confirmed.**
`13e47133` keeps a substantial (though not full) timing benefit, since
every pair happened to show the pattern on its first attempt in this run.
`0934a4d8` does not: one pair's first attempt was a false negative, and
because detection only ever checks attempt 0, that pair could not recover
and ended up slower than plain `baseline`. The conditional policy's
timing benefit is real but contingent on the first attempt being
representative of the pair, which failed for 1 of the 9 pairs measured
across the 2 target tasks (11%) in this sample.

## Consequences

- The regression this ADR set out to avoid (ADR 0030's -21% on the 6
  unaffected tasks) is resolved: mean held-out accuracy returns to within
  noise of `baseline`.
- The timing benefit this ADR set out to keep is not reliably delivered as
  implemented: it depends on every pair's first attempt being
  representative, and one pair in this sample was not, producing a net
  timing loss on `0934a4d8` rather than a gain.
- A concrete refinement is now visible for any next iteration: check every
  attempt for the pattern, not only attempt 0, and escalate as soon as any
  attempt so far in a pair shows it (still stopping short of checking
  every attempt of every pair under the mitigated config, which is what
  global `ngram_only` already does). Not implemented here, named as an
  open next step.
- Given Result 1's mixed outcome and Golden Rule 7 (a single 8-task sanity
  run cannot back a policy decision), this ADR does not propose Status:
  Accepted. The three now-compared decode strategies for the 2 target
  tasks (`baseline`, `ngram_only` global, `conditional` as implemented
  here) are presented for a joint decision, alongside the option of
  refining the conditional policy before it is tried again.
- Single run; TTT/LoRA initialization and sampling are stochastic (same
  caveat as ADR 0027/0029/0030), so exact figures, especially which
  specific pair lands on the adverse first-attempt case, are not expected
  to reproduce run to run.

## Alternatives considered

- Checking every attempt for the pattern (not just attempt 0) and
  escalating as soon as any attempt so far shows it: this is the direct
  fix for Result 3's adverse case, but was not implemented in this pass,
  since the task as specified was to test the exact policy ADR 0030 named
  (first attempt only). Recorded above as the concrete next refinement.
- Escalating for the rest of the *task* (all remaining pairs), not just
  the rest of the *pair*, once any pair shows the pattern: not
  implemented, since it would give up more of the regression-avoidance
  result (Result 2) than this ADR's data justifies changing; the per-pair
  scope kept the blast radius of a false positive to a single pair.
- Re-running `baseline` on all 8 tasks with matched TTT seeds to get an
  exact-second overhead figure for the 6 unaffected tasks (Result 4):
  not done, judged unnecessary given the structural argument (no extra
  generate() calls when not escalating) and the accuracy match; left open
  if the joint decision wants a directly measured figure.
