# 0036 - Cross-task pretraining pilot (real run, partial)

## Status

Informative. Reports a real, partially-completed ~150-task pilot run and
a timing-anomaly investigation. Does not decide whether to retry this
pilot, complete it, or scale cross-task pretraining ([ADR 0022](0022-hypothesis-reformulation-post-augmentation-discovery.md))
to the full 1000-task training corpus. That remains a separate, future
joint decision.

## Context

This ADR follows directly from [ADR 0035](0035-dimensionamento-pretreino-cross-task.md)'s
sizing pass and answers the request that motivated it: implement
checkpointing for a cross-task pretraining run, define a pretraining
task split disjoint from the reserved sanity/validation evaluation
tasks, and run an intermediate-scale (~100-200 task) pilot measuring
(1) held-out accuracy versus [ADR 0034](0034-first-validation-consolidated-config.md)'s
baseline, (2) total time versus ADR 0035's proportionally-scaled
estimate, and (3) whether checkpointing works via a deliberate
interrupt/resume test.

Two prerequisites (Parts 1 and 2 of that request) were built in earlier
sessions and are only summarized here, not re-described:

- **Checkpointing**: `checkpoint_utils.find_resumable_checkpoint` plus
  `checkpoint_save_strategy`/`checkpoint_save_steps` config fields,
  wired into `run_cross_task_pretraining_pilot.py`'s
  `_run_pretraining_phase` with `save_strategy="steps", save_steps=500`.
- **Disjoint pretraining split**: `pretraining_split.py`
  (`select_pretraining_tasks_excluding_reserved`, seed
  `DEFAULT_PRETRAINING_SEED=4242`), checked at runtime against
  `reserved_evaluation_task_ids()` (the union of the sanity and
  validation tiers), not just by directory convention.

Part 3, the real pilot run, is what this ADR reports.

## Decision

### Real pilot run: what happened

`run_cross_task_pretraining_pilot.py 150` was launched against 150
training-split tasks (seed 4242, manifest saved to
`outputs/diagnostics/cross_task_pretraining_pilot/pretraining_pilot_split.json`,
150 task ids confirmed) and the full 44-task reserved evaluation set.

**Pretraining phase completed successfully:**

- `Num examples = 11,760`, `Num Epochs = 1`, `Total steps = 5,880`,
  `per_device_train_batch_size=2`, `Trainable parameters = 39,976,960
  of 7,338,594,304 (0.54% trained)`.
- `train_runtime = 12,680s` (about 3h31min), `train_loss = 0.8482`.
- The adapter saved cleanly to `outputs/adapters/cross_task_pretrained`.

11,760 examples for 150 tasks is 78.4 examples/task, in line with ADR
0035's estimated 24x augmentation rate on this project's mean of
3.232 raw train pairs/task. This confirms ADR 0035's example-count
model directly: pretraining time scales with augmented example count,
not linearly with raw task count, an error self-caught and corrected
mid-run in this same session (an initial estimate wrongly scaled the
smoke check's 2-task pretraining time by task count alone, giving
~1.8h; the corrected, augmented-example-based estimate of ~3.2-3.5h
matched the eventual 12,680s measurement closely).

**Evaluation phase did not complete.** Reserved tasks are evaluated in
sorted-id order (`_select_eval_tasks`). Only 3 of 44 were measured
before the run was deliberately interrupted (see next section):

| Task | TTT runtime | Notes |
|---|---|---|
| `0934a4d8` | 181.6s | normal, in line with ADR 0034's per-task range |
| `135a2760` | 5000s | anomalous, see below |
| `136b0064` | 54.46s | normal |
| `13e47133` | interrupted, no result | in progress ~1h46min+ when killed |

Per-cell accuracy on the 3 completed tasks' held-out test pairs:
`0934a4d8` no result recorded for `constrained_best_cell_accuracy` on
its one test pair (`null` in the saved row), `135a2760` test pair
0.8561, `136b0064` test pair 0.6015. This is too small an n (2 held-out
test pairs with a recorded value) to compare against ADR 0034's
40-task/54-pair distribution in any statistically meaningful way; no
accuracy conclusion is drawn from it.

**Time versus ADR 0035's estimate:** pretraining alone (12,680s, about
3h31min) sits within ADR 0035's optimistic-to-pessimistic range
(8-60+ hours) once correctly scaled by augmented example count, not
task count. Total pilot time cannot be reported since the evaluation
phase did not finish; the run was manually interrupted after
approximately 6h51min of total wall-clock time (pretraining plus 3
completed and one partial evaluation), confirmed via
`ps -eo pid,lstart,etime,cmd` (started 09:02:41, checked 15:54).

**Checkpointing was not deliberately tested.** The pretraining phase's
`save_strategy="steps", save_steps=500` checkpoint mechanism was
implemented and active during this run, but the phase completed
unattended before a planned interrupt/resume test was carried out; no
mid-pretraining kill-and-resume was performed. This requirement (3) of
the original request is not yet fulfilled and is carried forward as
an explicit gap, not silently dropped.

### Timing anomaly recurrence and investigation

`135a2760` took 5000s in this real run, closely matching a nearly
identical anomaly (5947.97s) seen earlier in the smoke-scale check that
validated this same pilot script before the real run (documented
inline in that script's own docstring and rows, not a separate ADR).
That smoke-scale anomaly had already been investigated by a diagnostic
script (`diagnose_warm_start_timing_anomaly.py`) which ruled out three
candidate causes using the smoke check's adapter (pretrained on only 2
tasks): task content, the warm-start mechanism itself, and loop
position (second-attach degradation). That diagnostic did not
reproduce the anomaly under any of its four conditions and concluded
it was likely a one-off transient.

The real pilot run's recurrence directly contradicts that conclusion.
Presented with this contradiction, the user chose to interrupt the
running pilot and investigate before letting it continue or reducing
scope. The process was killed cleanly (`kill -TERM` on both the
wrapping shell and Python PIDs, confirmed via exit code 15, i.e. SIGTERM
as expected, not a crash).

This left one variable the prior diagnostic had not controlled for:
**adapter content**. The prior diagnostic ran and completed before the
real 150-task pretraining phase existed, so it could only reuse the
old 2-task-pretrained adapter at the same `ADAPTER_DIR` path, never the
adapter that the anomalous real run actually warm-started from. A new
diagnostic, `diagnose_real_adapter_timing_anomaly.py`, re-tested
`135a2760` alone using the real adapter, adding background `nvidia-smi`
sampling (every 5s: temperature, SM clock, throttle-reason bitmask,
power draw) to also catch GPU thermal/clock throttling as a candidate
confound, since that could not be captured retroactively after the real
run's process was already dead.

**Result: 122.43s, no reproduction.** Adapter content is ruled out as
the cause.

**GPU thermal/power log from that same run** (`outputs/diagnostics/real_adapter_timing_gpu_log.csv`):
temperature climbed from 45°C to 83°C over about 2 minutes of sustained
TTT load; power draw rose from idle (~13-15W) to a sustained ~150-157W,
close to this card's 160W software power limit; `clocks_event_reasons.active`
began alternating between `0x4` (SW Power Cap active) and `0x20` (SW
Thermal Slowdown active) once temperature passed roughly 74°C. This
confirms the GPU does enter genuine active throttling conditions under
sustained load on this hardware. SM clock, however, stayed high
(2625-2730 MHz) throughout, and total time was still normal (122.43s),
so throttling of this level and duration alone does not explain a
~40x-magnitude anomaly (122s versus 5000s).

**Summary of hypotheses tested:**

| Hypothesis | Status | Evidence |
|---|---|---|
| Task content (`135a2760` is inherently slow) | Ruled out | `diagnose_warm_start_timing_anomaly.py` round 1, fresh LoRA, no warm start: normal time |
| Warm-start mechanism itself | Ruled out | same diagnostic, round 2: normal time |
| Loop position (second attach/detach cycle) | Ruled out | same diagnostic, round 4: normal time on both tasks |
| Adapter content (old 2-task vs. real 150-task adapter) | Ruled out | `diagnose_real_adapter_timing_anomaly.py`: 122.43s, no reproduction |
| Short-duration thermal/power throttling | Insufficient alone | GPU log shows real throttle-reason flags under sustained load, but SM clock stays high and total time is still normal in this same run |
| Degradation specific to very long (3.5h+), continuous single-process GPU/CUDA sessions | **Untested, named as the remaining candidate** | neither isolated diagnostic ran long enough (each under ~5 minutes) to reproduce or refute this cheaply |

Five candidate causes are now ruled out or shown insufficient on their
own. The one remaining, most plausible hypothesis, that some form of
degradation accumulates specifically over very long continuous
GPU/CUDA sessions (memory fragmentation, driver-level state, or a
slower thermal/power effect than the 2-minute window sampled here can
show), was not tested further. Reproducing it cheaply would require a
synthetic multi-hour GPU load, a materially more expensive test than
either diagnostic run so far. Per the user's explicit decision, this
investigation is closed here and the hypothesis is recorded as a named,
unresolved risk rather than pursued to a confirmed root cause.

This follows the same project precedent as [ADR 0028](0028-timing-anomaly-and-task-complexity-investigation.md)/[0031](0031-conditional-ngram-mitigation.md)/[0032](0032-per-attempt-conditional-ngram-mitigation.md):
naming and characterizing a timing anomaly's evidence and boundaries
even when the underlying mechanism is not fully resolved, rather than
leaving it undocumented.

## Consequences

- Pretraining-time scaling is now confirmed empirically at real scale:
  time scales with augmented example count (11,760 examples, 5,880
  steps for 150 tasks), not raw task count, correcting a live
  estimation error and validating ADR 0035's sizing model.
- The disjoint-split and checkpointing implementations both work
  mechanically (the split manifest is correct and disjoint, the
  pretraining phase runs and saves cleanly), but the deliberate
  interrupt/resume test the original request asked for was never
  performed; this is an open gap, not a completed requirement.
- No accuracy comparison against ADR 0034's baseline is possible from
  this pilot; only 3 of 44 reserved tasks produced results, far too few
  and too partial to support any conclusion, positive or negative,
  about cross-task pretraining's effect on held-out accuracy.
- A named, unresolved risk now exists for future long GPU runs (a
  cross-task pretraining run at full 1000-task scale, or the eventual
  Kaggle submission run): TTT time can spike by roughly 40x on an
  individual task after hours of continuous GPU/process uptime, for a
  reason not yet identified. Any future long run should budget for this
  possibility (e.g. via a hard per-task time cap, or periodic process
  restarts) rather than assuming ADR 0034-style per-task timing holds
  indefinitely.
- Real GPU thermal/power headroom is now measured under sustained TTT
  load on this hardware: this card runs close to its 160W power limit
  and enters software power-cap/thermal-slowdown states within about 2
  minutes of sustained load, worth accounting for in any future
  long-run time budget even though it did not explain this specific
  anomaly.
- No decision is made on retrying this pilot, completing its evaluation
  phase, or scaling cross-task pretraining to the full corpus. That
  remains open, now informed by a real (if partial) timing measurement
  and a named, unresolved risk rather than a purely estimated range.

## Alternatives considered

- **Let the pilot keep running to completion despite the anomaly
  recurrence:** rejected by explicit user choice; the recurrence
  directly contradicted the prior diagnostic's conclusion and the user
  judged investigating it worth pausing the run for, rather than
  absorbing an unknown, possibly-recurring multi-thousand-second cost
  across the remaining 41 evaluation tasks.
- **Interrupt and immediately reduce evaluation scope (fewer reserved
  tasks) to get a faster, complete signal:** rejected in favor of
  investigating the anomaly first, since a reduced-scope run would
  still risk hitting the same unresolved anomaly on an unpredictable
  subset of tasks, without adding any diagnostic value.
- **Keep chasing the remaining untested hypothesis (long-session
  degradation) with a synthetic multi-hour reproduction:** rejected by
  explicit user choice; five of six candidate causes are already ruled
  out or shown insufficient, and confirming the sixth would cost GPU
  time disproportionate to what a named, documented risk already
  communicates for planning purposes.
- **Relaunch the full 150-task pilot from scratch now, accepting the
  anomaly risk, to get complete Part 3 metrics in this session:**
  rejected; per the user's decision to close this out via documentation,
  no further GPU-costly reproduction or full pilot run was initiated in
  this session.

## References

- [ADR 0013 - Time budget for 240 tasks](0013-time-budget-240-tasks.md)
- [ADR 0015 - Layered sampling](0015-layered-sampling.md)
- [ADR 0022 - Hypothesis reformulation after the pre-existing-augmentation discovery](0022-hypothesis-reformulation-post-augmentation-discovery.md)
- [ADR 0028 - Timing anomaly and task complexity investigation](0028-timing-anomaly-and-task-complexity-investigation.md)
- [ADR 0031 - Conditional no_repeat_ngram_size mitigation](0031-conditional-ngram-mitigation.md)
- [ADR 0032 - Per-attempt conditional no_repeat_ngram_size mitigation](0032-per-attempt-conditional-ngram-mitigation.md)
- [ADR 0034 - First validation-tier run of the consolidated config](0034-first-validation-consolidated-config.md)
- [ADR 0035 - Sizing the cross-task pretraining hypothesis](0035-dimensionamento-pretreino-cross-task.md)
