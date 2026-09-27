# 0039 - Cross-task pretraining pilot v2, paired comparison

## Status

Informative. Reports a real, completed paired comparison (same 12
held-out tasks, baseline vs. warm-started) and root-causes/fixes the
severe timing anomaly this run surfaced mid-execution. Does not decide
whether cross-task pretraining becomes production policy or is scaled
to the full 1000-task corpus. That remains a separate, future joint
decision.

## Context

[ADR 0036](0036-piloto-pretreino-cross-task.md)'s pilot completed
pretraining cleanly but its evaluation phase was interrupted after only
3/44 reserved tasks, so it produced no accuracy comparison against
[ADR 0034](0034-first-validation-consolidated-config.md)'s baseline.
Its own evaluation-phase design also could not have supported a valid
comparison even if completed: the baseline scenario used a different,
larger evaluation-task population than the pretraining pool's disjoint
split, so any accuracy delta would be confounded by which tasks were
sampled, not just by whether pretraining was applied.

This pilot (v2) fixes both gaps at a smaller, faster scale: 40
pretraining tasks (not 150), 12 reserved evaluation tasks (not 44), and
critically, a **paired design** - the same 12 tasks run under
`baseline_no_pretraining` (no adapter, ADR 0034/0037 config) and
`warm_started_from_pretraining_v2` (TTT warm-started from the freshly
pretrained cross-task adapter), so the only thing that differs between
the two scenarios is the presence of the pretrained adapter.

## Decision

### Run 1: baseline scenario and pretraining phase (completed cleanly)

`run_cross_task_pretraining_pilot_v2.py` selected 40 pretraining tasks
(seed 4242, disjoint from the reserved evaluation pool per ADR 0036's
split logic) and 12 reserved evaluation tasks (`eval_subsample_v2.json`:
`135a2760`, `20270e3b`, `28a6681f`, `3dc255db`, `4c416de3`, `7b5033c1`,
`8698868d`, `9bbf930d`, `a251c730`, `d59b0160`, `dbff022c`, `dfadab01`).

The baseline scenario and the pretraining phase both completed without
error: `ttt_total_seconds=2338.68` for the 12-task baseline,
`pretraining_seconds=2330.73` (about 38.8 minutes) for the 40-task
pretraining phase, adapter saved to
`outputs/adapters/cross_task_pretrained_v2/`.

### Bug found mid-run: a systemic 55-70x per-step slowdown, not ADR 0036's anomaly

The warm-started scenario was then launched and monitored. Within the
first two tasks it was running at roughly 60-79 seconds per training
step, versus baseline's roughly 1.1-1.2s/it, a 55-70x per-step
slowdown. This is a different failure signature from ADR 0036's
`135a2760`-specific spike: it was systemic across every warm-started
task from the start, not an isolated single-task anomaly. Surfaced to
the user, the explicit decision was to interrupt the run and
investigate the root cause before retrying, rather than let it run to
completion at that rate (which would have taken many hours) or reduce
scope.

**Root cause**: `lora_setup.attach_pretrained_lora` built the
warm-started adapter via a plain `peft.PeftModel.from_pretrained(...,
is_trainable=True)` call. Unsloth's fast fused Triton LoRA-MLP kernels
and gradient-checkpointing wiring are patched in specifically inside
`FastLanguageModel.get_peft_model` (what `attach_fresh_lora` calls, and
what the baseline scenario uses for every task). A bare
`PeftModel.from_pretrained` attaches a functionally equivalent but
unpatched adapter, silently bypassing that fast-path entirely and
falling back to slow, unfused execution.

**Fix**: `attach_pretrained_lora` now builds the adapter via
`attach_fresh_lora` (so it goes through `FastLanguageModel.get_peft_model`
and keeps the fast kernels) and then loads the pretrained weights into
that adapter via `peft.utils.load_peft_weights` +
`peft.set_peft_model_state_dict`, instead of replacing the adapter
object outright.

**Validated on real GPU** with a throwaway smoke script reusing the
already-trained v2 adapter (no re-pretraining needed): task `0934a4d8`
trained at ~1.15s/it, `train_runtime=191.1s` for 144 steps, matching
baseline's per-step speed. The fix was then exercised for real across
all 12 warm-started tasks in the full resume run below, with per-task
`train_runtime` values (110.1s for 72 steps, 165.1s for 144 steps, etc.)
consistently in the baseline's speed range and no recurrence of the
slowdown on any task.

### Retroactive reframing of ADR 0036's timing anomaly

ADR 0036 named "degradation specific to long continuous GPU/CUDA
sessions" as the one remaining, untested hypothesis for `135a2760`'s
5000s anomaly (versus a normal ~150-200s), after ruling out five other
candidates. That pilot used the same broken `attach_pretrained_lora`
code path this ADR fixes. A ~55-70x systemic slowdown from unpatched
Unsloth kernels is the same order of magnitude as that anomaly's ~25-40x
ratio to normal task time, and this pilot's full 12-task re-run with the
fix shows zero recurrence of any anomaly of that scale (worst case
287.96s total, in the normal range). This does not retroactively prove
ADR 0036's specific anomaly had this exact cause with certainty (no
diagnostic was re-run against that specific historical scenario), but it
is now the far more plausible explanation than an unresolved
long-session GPU degradation effect, and the "named, unresolved risk"
framing in ADR 0036 should be read as very likely closed by this fix,
not as a still-open risk requiring separate future budgeting.

### Resuming without repeating valid work

The interrupted warm-started run had already completed 11 of 12 tasks
(confirmed via output-file timestamps: continuous, genuine if very slow
progress over about 7.5 hours, not a hang) using the broken code. Its
accuracy results would likely be numerically equivalent to a fixed-code
re-run (same LoRA math, only the kernel path differs), but its **timing**
is invalid for this ADR's paired time-cost comparison. Rather than mix
execution paths, the entire warm-started scenario was discarded and
re-run fresh with the fix, while the already-valid baseline scenario and
pretrained adapter (both unaffected by this bug) were reused unchanged
via a new `resume_cross_task_pretraining_pilot_v2.py` script.

### Paired comparison results

| Metric | `baseline_no_pretraining` | `warm_started_from_pretraining_v2` |
|---|---|---|
| `exact_match_rate_test` | 0.0000 (0/13) | 0.0000 (0/13) |
| `per_cell_accuracy_test` mean | 0.7959 | 0.8015 |
| close / middling / far | 6 / 2 / 5 | 7 / 1 / 5 |
| `ttt_total_seconds` (12 tasks) | 2338.68 | 2152.30 |
| one-time pretraining cost | n/a | 2330.73 (40 tasks, amortized once) |

Per-task test-pair `constrained_best_cell_accuracy`, paired:

| Task | Baseline | Warm-started | Delta |
|---|---|---|---|
| `135a2760` | 0.7681 | 0.79 | +0.02 |
| `20270e3b` (x2 pairs) | n/a (parse failure) | n/a (parse failure) | unchanged |
| `28a6681f` | 0.92 | 0.73 | -0.19 |
| `3dc255db` | 0.8718 | 0.87 | ~0 |
| `4c416de3` | 0.8732 | 0.90 | +0.03 |
| `7b5033c1` | n/a (parse failure) | n/a (parse failure) | unchanged |
| `8698868d` | n/a (parse failure) | n/a (parse failure) | unchanged |
| `9bbf930d` | 0.9648 | 0.98 | +0.02 |
| `a251c730` | n/a (parse failure) | n/a (parse failure) | unchanged |
| `d59b0160` | 0.6172 (middling) | 0.73 (close) | +0.11, crosses band |
| `dbff022c` | 0.9349 | 0.87 | -0.06 |
| `dfadab01` | 0.4175 (middling) | 0.54 (middling) | +0.12, same band |

### Reading the result honestly

This is a **mixed, marginal result**, not a clear positive or negative:

- `exact_match_rate_test` is 0/13 in both scenarios; cross-task
  pretraining produced no new exact match on held-out data in this
  sample.
- Mean per-cell accuracy moves up by 0.0056 (0.7959 to 0.8015, about
  0.7% relative), almost entirely driven by one task (`d59b0160`)
  crossing from "middling" into "close". Two other tasks move down
  notably (`28a6681f` -0.19, `dbff022c` -0.06) while three move up
  slightly (`135a2760`, `4c416de3`, `9bbf930d`). This is consistent with
  noise on an n=8-measurable-pairs sample, not a clearly demonstrated
  systematic improvement.
- The 5 total-parse-failure pairs (across `20270e3b`, `7b5033c1`,
  `8698868d`, `a251c730`) are identical in both scenarios: cross-task
  pretraining did not fix any of them. Whatever gap keeps these tasks
  from producing a parseable/self-consistent answer at all is untouched
  by this lever.
- `ttt_total_seconds` for the 12-task warm-started scenario (2152.30s)
  came out lower than baseline (2338.68s), about 8% faster, even though
  both run the identical number of TTT steps per task (same augmented
  example count, same 3 epochs). This is very likely per-step timing
  variance between runs, not a real effect of warm-starting on training
  speed, since step count is fixed by config, not by convergence.
- The one-time pretraining cost (2330.73s, about 38.8 minutes for 40
  tasks) is a real, fixed overhead that would need to be paid once and
  amortized if this became a production lever. At this pilot's scale,
  that cost is not repaid by a proportionate accuracy gain.

No conclusion is drawn about whether a larger pretraining pool (closer
to ADR 0035's full 1000-task estimate) would show a stronger effect;
this pilot only tests the 40-task scale.

## Consequences

- The `attach_pretrained_lora` bug is fixed
  (`src/solvers/neural/lora_setup.py`) and validated on real GPU across
  13 task-runs (1 smoke test + 12 full warm-started scenario tasks) with
  zero recurrence of the slowdown.
- ADR 0036's "long continuous GPU session degradation" risk should be
  treated as very likely closed by this fix rather than an open item
  requiring separate mitigation in future long runs, though it was not
  re-tested against that exact historical scenario.
- The paired-comparison design (same task population, two scenarios) is
  now validated as a methodology and is a better fit than ADR 0036's
  original evaluation-phase design for any future retry of this
  hypothesis at a different scale.
- At 40 pretraining tasks, cross-task pretraining shows no exact-match
  gain, a small and largely single-task-driven per-cell-accuracy gain,
  and no effect on total parse-failure tasks, for a real ~39-minute
  fixed cost. This is not strong evidence either for or against
  investing further in ADR 0022's hypothesis; a materially larger
  pretraining pool (closer to ADR 0035's full-scale estimate) would be
  needed to test whether the effect strengthens with scale, which this
  pilot does not resolve.
- No production decision is made here, consistent with every prior
  cross-task pretraining ADR in this chain (0022/0035/0036).

## Alternatives considered

- **Reuse the interrupted run's 11/12 completed warm-started task
  results instead of re-running:** rejected. Their accuracy is likely
  equivalent to a fixed-code re-run, but their timing (recorded at
  55-70x the correct per-step rate) is not valid data for this ADR's
  explicit "total time per scenario" metric, and mixing one scenario's
  timing data across two different code paths would corrupt the
  comparison this pilot exists to make.
- **Re-run the full pretraining phase too, not just the warm-started
  scenario:** rejected as unnecessary cost. The pretraining phase and
  the baseline scenario both ran on the correct, already-fast code path
  (`attach_fresh_lora` throughout); only `attach_pretrained_lora`, used
  exclusively by the warm-started scenario, was affected.
- **Skip the real-GPU validation and trust the code fix based on reading
  Unsloth's source alone:** rejected; a smoke test confirming the actual
  measured per-step speed was cheap (about 3 minutes) relative to the
  risk of relaunching a multi-task run on an unverified fix.
- **Scale directly to the full 1000-task pretraining corpus now that the
  bug is fixed, skipping a second small-scale measurement:** rejected;
  per ADR 0022/0035/0036's established pattern, a production-scale
  investment is not made without an intervening measured signal, and
  this pilot's marginal result does not provide a strong basis for that
  jump.

## References

- [ADR 0022 - Hypothesis reformulation after the pre-existing-augmentation discovery](0022-hypothesis-reformulation-post-augmentation-discovery.md)
- [ADR 0034 - First validation-tier run of the consolidated config](0034-first-validation-consolidated-config.md)
- [ADR 0035 - Sizing the cross-task pretraining hypothesis](0035-dimensionamento-pretreino-cross-task.md)
- [ADR 0036 - Cross-task pretraining pilot (real run, partial)](0036-piloto-pretreino-cross-task.md)
- [ADR 0037 - Error pattern diagnosis on "close" held-out pairs](0037-diagnostico-padrao-erro-pares-close.md)
