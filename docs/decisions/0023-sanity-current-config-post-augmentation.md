# 0023 - Sanity run of the current mature config, post-augmentation

Status: Informative

## Context

ADR 0021/0022 left two questions open before choosing between refining
within-task augmentation further (color, more D4 variants) and
evaluating the bigger cross-task-pretraining hypothesis: both prior
results came from only 2 tasks (`136b0064`, `135a2760`). Per Golden
Rule 7, `smoke`-layer results never back a policy decision on their
own. Before that joint decision, this ADR runs the `sanity` layer
(8 tasks) with the current, mature default config (full 8-element D4
geometric augmentation, ADR 0021, plus the ADR 0010 EOS fix, both
already `NeuralSolverConfig()` defaults) to see whether ADR 0021's
2-task findings hold at a larger, still-diagnostic sample size.

## Method

New `src/evaluation/run_sanity_current_config.py`, reusing the shared
`src/evaluation/diagnostic_runner.py` (ADR 0021) unchanged except for
one addition: a `shape_matches_expected` field per pair (`None` if
nothing was kept to check, else whether at least one kept prediction
at least matches the expected output's grid shape, via the existing
`pair_diagnostics.dimension_match`), to tell "structurally close" apart
from "wrong every way" as requested. Fixed a latent host/GPU import
boundary violation in `diagnostic_runner.py` in the process (see
Consequences).

Task sample: `sample_tiers.select_tier_tasks(tasks, "sanity")`, the
same deterministic (no seed involved for this tier) first-8-tasks
selection ADR 0017 used, confirmed to select the identical 8 task IDs
and the identical `test_pairs_total = 11` ADR 0017 reports, so this
result is directly comparable to ADR 0017, not a new sample.

Ran 2026-09-07, evaluation split, single config (`current_config` =
bare `NeuralSolverConfig()` defaults, no overrides).

## Result

Full per-pair table (20 train pairs + 11 test pairs, 8 tasks):

| Config | Task | Split | Pair | Attempts | Parsed | Kept | Copies of input | Exact match | Shape match |
|---|---|---|---|---|---|---|---|---|---|
| current_config | 0934a4d8 | train | 0 | 4 | 2 | 2 | 0 | no | no |
| current_config | 0934a4d8 | train | 1 | 6 | 1 | 1 | 0 | no | no |
| current_config | 0934a4d8 | train | 2 | 6 | 1 | 1 | 0 | no | no |
| current_config | 0934a4d8 | train | 3 | 6 | 1 | 1 | 0 | no | no |
| current_config | 0934a4d8 | test | 0 | 2 | 2 | 2 | 0 | no | no |
| current_config | 135a2760 | train | 0 | 2 | 2 | 2 | 1 | no | yes |
| current_config | 135a2760 | train | 1 | 2 | 2 | 2 | 0 | no | yes |
| current_config | 135a2760 | test | 0 | 2 | 2 | 2 | 0 | no | no |
| current_config | 136b0064 | train | 0 | 2 | 2 | 2 | 0 | no | no |
| current_config | 136b0064 | train | 1 | 2 | 2 | 2 | 0 | no | no |
| current_config | 136b0064 | train | 2 | 2 | 2 | 2 | 0 | no | no |
| current_config | 136b0064 | test | 0 | 2 | 2 | 2 | 0 | no | no |
| current_config | 13e47133 | train | 0 | 2 | 2 | 2 | 0 | no | no |
| current_config | 13e47133 | train | 1 | 2 | 2 | 2 | 0 | no | no |
| current_config | 13e47133 | train | 2 | 6 | 0 | 0 | 0 | no | n/a |
| current_config | 13e47133 | test | 0 | 5 | 2 | 2 | 0 | no | no |
| current_config | 13e47133 | test | 1 | 4 | 2 | 2 | 0 | no | no |
| current_config | 142ca369 | train | 0 | 2 | 2 | 2 | 0 | no | no |
| current_config | 142ca369 | train | 1 | 2 | 2 | 2 | 0 | no | no |
| current_config | 142ca369 | train | 2 | 2 | 2 | 2 | 0 | no | no |
| current_config | 142ca369 | test | 0 | 2 | 2 | 2 | 0 | no | no |
| current_config | 142ca369 | test | 1 | 2 | 2 | 2 | 0 | no | no |
| current_config | 16b78196 | train | 0 | 2 | 2 | 2 | 0 | no | no |
| current_config | 16b78196 | train | 1 | 3 | 2 | 2 | 0 | no | no |
| current_config | 16b78196 | test | 0 | 3 | 2 | 2 | 0 | no | no |
| current_config | 16de56c4 | train | 0 | 2 | 2 | 2 | 0 | no | yes |
| current_config | 16de56c4 | train | 1 | 2 | 2 | 2 | 0 | no | yes |
| current_config | 16de56c4 | train | 2 | 2 | 2 | 2 | 0 | no | yes |
| current_config | 16de56c4 | test | 0 | 3 | 2 | 2 | 0 | no | yes |
| current_config | 16de56c4 | test | 1 | 3 | 2 | 2 | 0 | no | no |
| current_config | 1818057f | train | 0 | 4 | 4 | 2 | 1 | no | yes |
| current_config | 1818057f | train | 1 | 2 | 2 | 2 | 0 | no | yes |
| current_config | 1818057f | train | 2 | 3 | 3 | 2 | 1 | no | yes |
| current_config | 1818057f | test | 0 | 2 | 2 | 2 | 0 | no | no |

Timing:

| Config | Task | TTT seconds | Total seconds |
|---|---|---|---|
| current_config | 0934a4d8 | 95.41 | 509.86 |
| current_config | 135a2760 | 29.89 | 109.02 |
| current_config | 136b0064 | 26.26 | 61.47 |
| current_config | 13e47133 | 41.55 | 1471.33 |
| current_config | 142ca369 | 41.42 | 225.49 |
| current_config | 16b78196 | 48.40 | 455.29 |
| current_config | 16de56c4 | 26.02 | 99.05 |
| current_config | 1818057f | 30.84 | 118.81 |

### Comparison against ADR 0017 (same 8 tasks, same 11 test pairs)

ADR 0017 could not distinguish parsing failure from content failure -
`_passes_self_consistency` rejected every task, all candidate files
were `[[]]`. This run, using the raw-text-capturing diagnostic path
instead of the production harness, closes that gap directly: **parsing
now succeeds on all 11/11 test pairs** (`kept = 2` on every one), a
concrete, positive result ADR 0017 could not see.

### Answering the two questions this run was designed for

**(a) Does the copy-paste pattern reappear at n=8, or does ADR 0021's
2-task finding hold?** Held-out test pairs: it holds. All 11/11 test
pairs show `num_copies_of_input: 0`. The pattern does reappear, but
only on **training** pairs, and only for 2 of 8 tasks: `135a2760`
train-0 (copies=1) and `1818057f` train-0 and train-2 (copies=1 each).
So the precise, narrower claim survives at n=8 (no copy-paste on
held-out input); the broader claim ("copy-paste is gone") does not -
it is still present on 3/20 training pairs.

**(b) Did any exact_match appear, even 1 in 8?** No. **0/31 pairs**
(11 test + 20 train) show `exact_match: yes`, across all 8 tasks. This
is itself a new, informative data point: ADR 0019 found one exact
match on a training pair, but only under `epochs_x2`, a config change
this run does not include. The current default config alone does not
even reproduce that narrower training-pair overfit at n=8.

### New signal not asked for directly, but relevant

`shape_matches_expected` (new this run): only **1 of 11 test pairs**
(`16de56c4` test-0) has a kept prediction whose grid shape matches the
expected output at all. The other 10/11 test pairs are wrong in both
structure and content. On train pairs, shape matches more often (9/20),
concentrated in 3 tasks (`135a2760`, `16de56c4`, `1818057f`) that
happen to have simple/repeated shapes across their own pairs. This
suggests the model doesn't reliably infer output *dimensions* from
train pairs it wasn't directly trained on, a more basic gap than
content correctness alone.

Timing shows a new, unresolved anomaly distinct from ADR 0021's
GPU-warmup confound: two tasks (`0934a4d8`, `13e47133`) show a
generation-time gap (`total_seconds - ttt_seconds`) far larger than
the other six (414s and 1430s respectively, vs. 35-407s elsewhere) that
does not track cleanly with attempt count alone (`13e47133`'s 19 total
attempts average ~75s/attempt vs. `0934a4d8`'s 24 attempts at
~17s/attempt). Not explained by this data; flagged, not investigated
further here.

## Decision

No lever is decided here, per the explicit instruction this run was
requested under. This is a diagnostic result only, per Golden Rule 7.

## Consequences

- Confirms, at n=8 (still short of the `validation` layer's 30-50), that
  ADR 0021's held-out no-copy-paste finding is not a 2-task fluke, while
  also showing the copy-paste failure mode is not fully eradicated (it
  survives on some training pairs).
- Confirms parsing/format reliability generalizes to n=8 (11/11 test
  pairs parse), a genuinely positive result this ADR is the first to
  show at this sample size.
- Adds a new, previously unmeasured gap: output grid *shape* is wrong
  on 10/11 held-out test pairs, not just content. Any future joint
  decision (color augmentation, D4-variant count, cross-task
  pretraining) should account for this, since a content-only fix would
  not address a wrong-shaped grid.
- Fixed a latent bug exposed while building this diagnostic, unrelated
  to the sanity result itself: `diagnostic_runner.py` imported
  `lora_setup` (which imports `unsloth`) at module top level, breaking
  host-Python (`unsloth`-free) test collection once a test file first
  imported the module directly. Moved to a lazy import inside
  `diagnose_task()`. Full suite: 83/83 passing on both host Python 3.8
  and the WSL `.venv312` Python 3.12.
- CLAUDE.md Section 6 updated to reflect this result instead of ADR
  0021's 2-task-only framing.

## Alternatives considered

- **Run at the `validation` layer directly instead of `sanity`:**
  rejected, per Golden Rule 7 a `sanity` result is the appropriate
  intermediate check before spending validation-tier compute, and this
  was the user's explicit request.
- **Decide the next lever now based on this result:** rejected per the
  user's explicit instruction; this ADR presents the result for a joint
  decision, it does not make one.

## References

- [ADR 0015 - Layered sampling](0015-layered-sampling.md)
- [ADR 0017 - Post-EOS-fix sanity diagnosis](0017-post-eos-fix-sanity-diagnosis.md)
- [ADR 0018 - Post-EOS-fix parsing-vs-content diagnosis](0018-post-eos-fix-parsing-vs-content-diagnosis.md)
- [ADR 0019 - Hyperparameter ablation on input-copying behavior](0019-hyperparameter-ablation-input-copying.md)
- [ADR 0020 - Next accuracy lever: data augmentation, not hyperparameter tuning](0020-lever-decision-data-augmentation.md)
- [ADR 0021 - Geometric augmentation smoke test](0021-augmentation-geometric-smoke-test.md)
- [ADR 0022 - Hypothesis reformulation after the pre-existing-augmentation discovery](0022-hypothesis-reformulation-post-augmentation-discovery.md)
