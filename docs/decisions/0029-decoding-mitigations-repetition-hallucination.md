# 0029 - Decoding mitigations for repetition and hallucination

## Status

Informative. Implements two independently-flagged, decode-level
mitigations for the two failure modes ADR 0028 diagnosed
(`13e47133`'s degenerate token repetition, `0934a4d8`'s hallucinated
second example), and reports a smoke-tier comparison. Does not decide
whether either mitigation becomes a production default.

## Context

ADR 0028 found that `0934a4d8` and `13e47133`'s recurring timing
anomaly (ADR 0023/0026/0027) is squarely in the generation retry loop:
both tasks repeatedly exhaust the 6-attempt cap on completions that
never terminate concisely, degenerate repetition for `13e47133`,
a hallucinated second `Input:`/`Output:` example for `0934a4d8`. It
named a generation-side fix as the next candidate lever, pending its
own ADR.

This ADR implements two cheap, no-retraining mitigations at the decode
layer:

1. `repetition_penalty` (1.3) and `no_repeat_ngram_size` (3) passed to
   `model.generate()`, targeting `13e47133`'s literal token repetition.
2. A stop-on-second-`Input:` heuristic: post-process truncation of the
   decoded completion at the first occurrence of the prompt's own
   `\nInput:` delimiter, targeting `0934a4d8`'s hallucinated
   continuation.

## Method

Both mitigations are independent `NeuralSolverConfig` fields
(`src/solvers/neural/config.py`), off by default at HF's own neutral
values (`repetition_penalty=1.0`, `no_repeat_ngram_size=0`,
`stop_on_second_input=False`), wired into
`_generate_completion` (`src/solvers/neural/generation.py`). The
stop heuristic is implemented as string truncation on the decoded
completion, not a custom `StoppingCriteria`, since it only needs to
read text already available after `generate()` returns and keeps the
change host-testable without a GPU dependency.

Four configs (`src/evaluation/decoding_mitigation_configs.py`):
`baseline`, `repetition_only`, `stop_heuristic_only`, `both`.

Two-part smoke-tier run (`src/evaluation/run_decoding_mitigations_smoke.py`,
`src/evaluation/mitigation_diagnostics.py`), shape constraint (ADR
0025/0026) kept applied throughout, same as ADR 0027/0028's reads:

- The two affected tasks, all four configs (isolates each mitigation's
  individual and combined contribution).
- The other 6 tasks from the same sanity sample (ADR 0017/0023/0026/0027),
  `baseline` and `both` only, as a regression check on tasks that never
  showed either failure mode. Rejected running all four configs on
  these 6 as well, to bound GPU time for what is meant to be a cheap
  smoke check; the question there is only whether the combined,
  production-candidate state changes their behavior, not each
  mitigation's isolated contribution, which the two affected tasks
  already answer.

`failure_mode_diagnostics.py` counts, across every raw attempt (not
just kept predictions), whether it contains the hallucination marker
or a run of 10+ identical consecutive lines. One caveat that shaped
reading the results: when `stop_on_second_input` is on, the returned
completion has already been truncated before this count runs, so a
hallucination count of 0 there reflects the final text only, not
proof the model never attempted to continue past its answer.

## Results

### 1. Does the failure mode disappear?

`13e47133` (degenerate repetition), attempts flagged repetitive out of
attempts tried, across its 5 pairs:

| Config | Repetitive attempts | Total attempts |
|---|---|---|
| `baseline` | 17 | 19 |
| `repetition_only` | **0** | 16 |
| `stop_heuristic_only` | 16 | 17 |
| `both` | **0** | 18 |

`repetition_penalty`/`no_repeat_ngram_size` eliminate the pattern
completely in this run (17/19 attempts down to 0), including the exact
pair ADR 0028 called out as a total parse failure (`train` pair 2,
`attempts_tried=6, num_kept=0` under `baseline`, resolved to
`attempts_tried=2, num_kept=2` under `repetition_only`). The stop
heuristic alone barely moves this count (17 to 16), as expected: it
targets a different text pattern entirely, not repeated rows.

`0934a4d8` (hallucinated second example), attempts flagged hallucinated:

| Config | Hallucinated attempts | Total attempts |
|---|---|---|
| `baseline` | 7 | 17 |
| `repetition_only` | 3 | 19 |
| `stop_heuristic_only` | 0 (by construction, see caveat above) | 18 |
| `both` | 0 (by construction) | 13 |

`repetition_only` alone also reduces this pattern substantially (7 to
3 attempts, including eliminating the worst pair's 5/6 hallucinated
attempts entirely), even though it was designed for the other task's
failure mode; a plausible mechanism is that discouraging repeated
tokens also discourages the model from reproducing the
`Output:`/`Input:` structural tokens it just emitted. `stop_heuristic_only`'s
0 count cannot be read as "prevented", since the truncation removes
the marker from the text before this count runs; `total attempts`
staying close to `baseline` (18 vs. 17) under `stop_heuristic_only`
shows it did not meaningfully reduce how often generation still needed
retrying.

### 2. Does generation time drop for the two affected tasks?

| Config | `0934a4d8` total seconds | `13e47133` total seconds |
|---|---|---|
| `baseline` | 312.50 | 1459.41 |
| `repetition_only` | 114.68 | 112.01 |
| `stop_heuristic_only` | 387.40 | 1359.17 |
| `both` | 87.43 | 126.32 |

Yes, dramatically, but almost entirely from mitigation 1: `repetition_only`
alone already captures nearly all of `both`'s benefit (a 3.6x reduction
for `0934a4d8`, an 11.5x reduction for `13e47133`).
`stop_heuristic_only` alone provides no reliable benefit, it is within
noise of `baseline` for `13e47133` (1359s vs. 1459s) and actually
slower for `0934a4d8` (387s vs. 312s). The mechanism: `stop_heuristic_only`
truncates the returned text after `model.generate()` has already run
to completion, so a call that would have hallucinated still pays its
full generation cost, only the parsed/kept result changes. `repetition_only`
changes the sampling process itself, so individual calls finish
sooner (shorter completions, earlier natural EOS), which is why total
attempts for `0934a4d8` under `repetition_only` (19) is not lower than
`baseline` (17), yet wall time drops 3.6x: attempts_tried does not
track wall time here, individual completion length does.

### 3. Does `13e47133`'s content quality change?

Held-out test pairs, per-cell accuracy: `baseline` 0.12/0.17 ->
`repetition_only` 0.14/0.18 -> `stop_heuristic_only` 0.12/0.03 (worse
on one pair) -> `both` 0.16/0.18. `exact_match` stays "no" everywhere
in every config. Essentially flat, a marginal improvement at most,
consistent with ADR 0028's reading that the repetition loop is a
symptom of low model confidence on this task's transformation, not its
cause; stopping the loop from consuming the retry budget does not by
itself teach the model the right transformation.

### 4. Regression check on the other 6 tasks

Timing improves for every one of the 6 tasks under `both` (roughly
1.3x to 4.3x faster), consistent with `repetition_only`'s general
effect of shortening completions. But held-out per-cell accuracy
regresses on every task where it is measurable:

| Task | Test pair(s), `baseline` -> `both` |
|---|---|
| `135a2760` | 0.77 -> 0.54 |
| `136b0064` | n/a -> n/a (shape rule fails, unaffected) |
| `142ca369` | 0.45 -> 0.31, 0.82 -> 0.73 |
| `16b78196` | 0.89 -> 0.76 |
| `16de56c4` | 0.59 -> 0.56, 0.73 -> 0.69 |
| `1818057f` | 0.90 -> 0.52 |

Mean across the 7 measurable held-out pairs: 0.736 -> 0.587 (-0.15,
about 20% relative). This is a real regression, not noise-sized: every
single measurable pair drops, `1818057f`'s single test pair drops the
most (-0.38). No `exact_match` appears or disappears anywhere (0 in
both configs). Training-pair accuracy drops by a similar or larger
margin for the same tasks. The likely mechanism: these 6 tasks were
already generating mostly-correct completions under `baseline`;
`no_repeat_ngram_size=3` forcibly blocks any 3-token sequence from
repeating verbatim, which can break a correct grid that legitimately
needs to repeat a short digit sequence (e.g. a run of the same color),
and `repetition_penalty=1.3` pushes the same direction more softly.
This ADR cannot separate which of the two parameters drives the
regression, since `repetition_only` varies both together; that split
is unresolved here.

So "no regression on the other 6 tasks" does **not** hold for `both`
as tested: generation gets substantially faster, but at a real,
consistent content cost on tasks that never had a timing or repetition
problem to begin with.

## Consequences

- Mitigation 1 (`repetition_penalty`/`no_repeat_ngram_size`) is the
  effective one for both target failure modes and both target tasks'
  timing; mitigation 2 (`stop_on_second_input`) provides negligible
  wall-time benefit as implemented, since post-hoc truncation does not
  shorten the underlying `model.generate()` call it truncates.
- Mitigation 1's benefit is not free: it measurably hurts held-out
  accuracy (-0.15 mean per-cell) on the 6 tasks that had no failure
  mode to fix. A task-conditional application (only for tasks actually
  showing the repetition pattern), gentler parameter values, or
  isolating `repetition_penalty` from `no_repeat_ngram_size` are all
  open, undecided directions.
- Whether either mitigation becomes a production default, in what
  form (global, conditional, different parameter values), is left to
  the joint decision that follows this ADR, per its explicit scope.
  Per Golden Rule 7, this smoke-tier result (n=2 primary tasks, n=6
  regression check) cannot by itself justify that decision either way.
- If mitigation 1 (or a refined, task-conditional version of it) is
  adopted, it would substantially cut the timing risk ADR 0027/0028
  flagged for a future `validation`-layer run: `0934a4d8`/`13e47133`
  together dropped from 1772s to 214s total generation time under
  `both`, removing most of the outlier cost a 30-50 task sample would
  otherwise have to budget for.
- A single run per config; TTT/LoRA initialization and sampling are
  stochastic, so exact figures are not expected to reproduce bit for
  bit (same caveat as ADR 0027), only the qualitative pattern.

## Alternatives considered

- Implementing the stop heuristic as a custom `StoppingCriteria` that
  halts `generate()` mid-decode instead of truncating after the fact:
  would likely have captured the wall-time benefit this post-hoc
  version misses (Result 2), since the call itself could return early.
  Not implemented here, kept the change host-testable and simpler for
  this first comparison; worth revisiting if `stop_on_second_input` is
  pursued further, now that this run shows the post-hoc version's
  timing benefit is negligible.
- Testing `repetition_penalty` and `no_repeat_ngram_size` as two
  separately-flagged mitigations instead of one combined "repetition"
  axis: rejected for this first pass, per the user's framing of them as
  one mitigation for one failure mode; Result 4's regression makes
  isolating them a natural next question, not addressed here.
- Running all four configs on all 8 sanity tasks: rejected to bound
  GPU time for a smoke-tier check; the two affected tasks already
  isolate each mitigation's individual contribution, the other 6 only
  needed the combined-state comparison.
