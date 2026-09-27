# 0035 - Sizing the cross-task pretraining hypothesis

## Status

Informative. Planning/estimation only. No code, config, or training
artifact is created by this ADR. This answers five explicit sizing
questions to support a future joint decision on whether to build a
cross-task pretraining phase (ADR 0022) ahead of per-task TTT, it does
not make that decision.

## Context

ADR 0034 gave the first real validation-tier evidence bearing on ADR
0022's candidate hypothesis: even with full in-task augmentation
(geometric + color) and the ADR 0032 decode escalation, 0/54 held-out
test pairs reach `exact_match` and mean held-out per-cell accuracy is
bimodal, not concentrated. Two distinct metrics from that ADR matter
here and must not be conflated:

- `per_cell_accuracy_test`'s far band: **22/54 (40.7%) of held-out
  pairs**, not tasks.
- `far_outlier_tasks`: **12/40 (30.0%) of tasks** (any train-pair
  `constrained_best_cell_accuracy` missing or below 0.3).

Both readings point the same direction (a large minority of the
sample shows a profile no augmentation or decode-level lever tested so
far has touched), but they are different denominators and are kept
separate below.

Before investing in building a cross-task pretraining phase, a
realistic sizing pass is needed. This ADR answers the five questions
asked, using real project data where available and explicit,
non-falsely-precise ranges where extrapolation is required.

## Decision

### 1. Volume de dados

Real counts from `data/ARC-AGI-2/data/` (downloaded per
[ADR 0005](0005-ai-assistant-usage-in-development.md)):

- **1000** public training task files, **3232** total train pairs
  across them (mean 3.232/task, median 3.0, min 2, max 10).
- 120 evaluation task files (not counted here; those are held out for
  the harness, not a pretraining source).

The current per-task augmentation stack ([ADR 0021](0021-augmentation-geometric-smoke-test.md)
geometric, [ADR 0027](0027-color-augmentation-sanity.md) color)
multiplies each raw train pair by **8 (geometric D4 transforms) x 3
(1 original + 2 color variants) = 24x**.

Applying that same rate across all 1000 training tasks:

```
3232 raw train pairs x 24 = 77,568 estimated augmented training examples
```

This is about **1/40th of NVARC's reported 3.2M-example corpus**
(103k tasks). Our public ARC-AGI-2 training set is roughly 10x smaller
in task count than NVARC's corpus, and at the same per-task
augmentation rate the example count comes out roughly 40x smaller, not
10x, because our tasks average fewer raw pairs/task (3.232) than
whatever NVARC's underlying rate implies. This is a real, measured gap
in scale, not just a rounding difference, worth carrying into question
2 explicitly.

### 2. Tempo de treino estimado

Empirical basis, parsed directly from
`outputs/diagnostics/validation_consolidated_config_run.log` (the same
40-task run ADR 0034 reports on):

- Mean TTT-only time: **111.26s/task** (range 52.48-227.79s), for a
  mean of ~77.6 augmented examples/task (3.232 raw pairs x 24) trained
  over `ttt_num_epochs=3` at `per_device_train_batch_size=2`.
- That implies roughly **0.48s per example-epoch** at the current
  per-task batch size and hyperparameters.

Scaling this rate naively to the full corpus (77,568 examples x 3
epochs = 232,704 example-epochs) gives an order-of-magnitude estimate,
**not a measurement**: two effects push in opposite directions and
neither has been tested.

- **Pushes time up:** a single cross-task run is a fundamentally
  different regime (one long, diverse, unbatched-by-task corpus versus
  1000 short, narrow, single-task runs); it is not established that 3
  epochs is enough to learn anything useful from data this
  heterogeneous, more epochs might be needed.
- **Pushes time down:** doing this once eliminates the ~1000x
  redundant per-task setup cost (LoRA attach, `Trainer`
  re-initialization, tokenization) that the current per-task rate
  necessarily includes; a single run also amortizes GPU warmup once
  instead of on every task.

Given both effects are unmeasured and the 8GB VRAM budget leaves
little room to grow the batch size much beyond the current
`per_device_train_batch_size=2` (ADR 0016 already measured 5.59/8GiB
peak on a single worst-case task), this ADR gives a wide range instead
of a false point estimate:

- **Optimistic:** ~8-15 hours (a single extended run, some efficiency
  gain from eliminating per-task setup overhead, 1-2 epochs).
- **Pessimistic:** ~30-60+ hours (no efficiency gain over the current
  per-example-epoch rate, 3+ epochs needed for the larger/more diverse
  corpus, spread across multiple sessions with checkpoint/resume).

Either bound is a materially larger single GPU commitment than
anything run so far in this project (the longest real run to date is
ADR 0034's ~3.0 hours for 40 tasks); the pessimistic bound alone would
exceed that by a factor of 10-20x, and would need to fit alongside,
not instead of, the remaining validation-tier and accuracy work before
November.

### 3. Mudança de arquitetura necessária

Current flow, confirmed by reading
`src/solvers/neural/model_loader.py`, `lora_setup.py`,
`ttt_trainer.py`, and `neural_solver.py`:

1. `model_loader.load_base_model` loads the frozen OSAID base
   (OLMo-2-1124-7B, 4-bit) once per process, cached at module level in
   `neural_solver._get_base_model`.
2. Per task: `lora_setup.attach_fresh_lora` wraps the frozen base with
   a brand-new PEFT adapter, always starting from the same base
   weights, no state carried over between tasks.
3. `ttt_trainer.train_on_task` builds this task's own augmented
   training texts and trains via HF `Trainer` for `ttt_num_epochs`
   (currently 3).
4. Self-consistency check, generation, `lora_setup.detach_lora`
   (`model.unload()`) returns to the frozen base for the next task.

A cross-task pretraining phase introduces a new artifact between "base
model" and "per-task TTT": something learned once across many tasks
that becomes the starting point per-task TTT further fine-tunes,
instead of starting fresh from the vanilla base every time. Open design
decisions this would require, **named but not resolved here**:

- **Where the cross-task learning lives.** (a) A separately-trained
  LoRA adapter, loaded as the initial adapter state before each
  per-task TTT (LoRA-on-top-of-LoRA), or (b) merge that adapter into
  the base once (`merge_and_unload`) producing a new "warmed" base
  checkpoint, with `lora_setup.py`'s existing attach/detach logic
  otherwise untouched. Option (b) keeps more of the current code
  unchanged but means keeping two base checkpoints on disk (the
  original OSAID base and the warmed one), interacting with the
  existing Qwen3-4B-removal trigger logic in CLAUDE.md Section 6.
- **Task-boundary handling during the pretraining run itself.** how
  tasks get batched/shuffled together, whether task identity is
  signaled in the prompt, whether a task's own pairs stay contiguous
  or get fully shuffled across the 77,568-example corpus.
- **A held-out split for the pretraining phase itself**, distinct from
  each task's own train/test split and from ADR 0015's smoke/sanity/
  validation tiers (which sample tasks for the per-task evaluation
  harness, not for a corpus-level training run). Without this, there
  is no way to tell whether cross-task training generalizes versus
  memorizes the 1000-task corpus.
- **Checkpointing and resumability.** Today's `_build_training_args`
  hardcodes `save_strategy="no"` because a per-task run finishes in
  under 5 minutes and never needs to resume. A run in the 10s-of-hours
  range (question 2) cannot use that setting; losing a 20-40 hour run
  to a crash would be a serious, avoidable cost.
- **Where the new code lives.** Per CLAUDE.md's file-per-responsibility
  rule, this is at least one new module (a corpus builder iterating
  all 1000 tasks, a training entry point distinct from
  `ttt_trainer.py`'s per-task path), not a modification of the
  existing per-task files.

### 4. Risco e reversibilidade

If the cross-task artifact is kept as a separate LoRA checkpoint or a
distinctly-named warmed base directory (design option 3a or a
distinct-directory version of 3b above), abandoning it requires **no
change to `lora_setup.py`, `ttt_trainer.py`, or `neural_solver.py`** -
only `model_loader.py`'s checkpoint path/config would need to point
back at the original frozen base, a one-line config change. The
current per-task pipeline stays intact and untouched throughout the
experiment.

The real, non-reversible cost of abandonment is sunk GPU time (the
pretraining run itself, per question 2's range) and disk space for
checkpoint artifacts, plus the calendar time spent building and
debugging the new corpus-builder and training-loop code. That
engineering work does not disappear on abandonment, but it also does
not corrupt or require rewriting anything in the currently-working
pipeline; it is additive risk, not destructive risk.

The one way this would stop being cheaply reversible: if the warm-start
selection logic were folded directly into `ttt_trainer.py`'s per-task
training path instead of staying isolated at the model-loading boundary
(`model_loader.py`). Keeping that boundary clean is itself a design
decision worth deciding explicitly, precisely because it is what keeps
this reversible.

### 5. Estimativa de calendário

Real observed pace, from file timestamps: ADR 0001
(2026-09-06 13:40) through ADR 0034 (2026-09-08 22:44) spans about
**2 days and 9 hours** of elapsed calendar time, covering the entire
current pipeline (base model swap, full augmentation stack, shape
constraint, four rounds of decode-mitigation tuning, and a real
~3-hour/40-task validation GPU run) - 34 ADRs in that span, averaging
roughly one every 1.7 hours.

That pace was achieved on **incremental, reversible changes to an
already-built pipeline** (config flags, decode parameters, prompt
construction), where the longest single GPU commitment so far is
ADR 0034's ~3.0 hours. A cross-task pretraining phase is structurally
different work: new corpus-building code across 1000 tasks, a new
checkpointed training entry point, a new held-out split, and (per
question 2) a training run itself 10-20x longer in wall-clock GPU time
than anything run to date.

Given that gap, a realistic estimate for a first **testable** version
(smoke/sanity-scale only, e.g. a 10-20 task subset instead of all
1000, just to prove the code path runs end-to-end, not the full
77,568-example run) is **2-4 calendar days** at this project's
demonstrated pace, most of it spent on the new code rather than on GPU
time (a smoke-scale run itself would take minutes). Reaching a
**finished** full-scale pretraining run is a separate, larger
commitment dominated by the GPU wall-clock range in question 2
(roughly 8-60+ hours), which competes directly with the remaining
validation-tier and accuracy work still needed before the
2026-11-02 deadline.

## Consequences

- A concrete, sourced answer now exists for all five sizing questions,
  usable in the next joint decision on whether to pursue ADR 0022's
  hypothesis, without committing to it here.
- The scale gap versus NVARC (77,568 estimated examples here vs. their
  reported 3.2M) is now explicit: this project's public training set
  is meaningfully smaller, and any expectation of NVARC-like results
  should be tempered by that gap, not assumed to transfer directly.
- The training-time range (8-60+ hours) is wide by design, per the
  user's own instruction against false precision; a real measurement
  (even a small-scale timed pilot, e.g. 20-50 tasks through the same
  corpus-builder code path) would narrow it substantially before a
  full commitment, and is a natural candidate first step if this
  hypothesis is pursued.
- No code, config, or ADR-tracked architecture change happens as a
  result of this ADR. `NeuralSolverConfig`, `model_loader.py`,
  `lora_setup.py`, and `ttt_trainer.py` are unchanged.

## Alternatives considered

- **Estimating a single point value for training time instead of a
  range:** rejected per explicit user instruction ("Dê uma faixa
  (otimista/pessimista), não um número falso de preciso"); the
  per-example-epoch rate measured so far comes from a regime (short,
  narrow, per-task runs) different enough from the proposed one (one
  long, diverse, corpus-wide run) that a single extrapolated number
  would carry false confidence.
- **Deciding the design questions in section 3 now, since they have an
  apparent lower-risk default (a separate LoRA/checkpoint, per section
  4's reversibility framing):** rejected; the user asked this ADR to
  name the decisions, not make them, reserving that for the joint
  decision this sizing pass is meant to support.
- **Running a small timed pilot as part of this ADR to replace the
  estimated range with a measured one:** rejected as out of scope; the
  user's instruction was explicitly "não implemente nada ainda, só
  estime", and a pilot run would require new training code this ADR is
  not authorized to write.

## References

- [ADR 0005 - AI assistant usage in development](0005-ai-assistant-usage-in-development.md)
- [ADR 0013 - Time budget for 240 tasks](0013-time-budget-240-tasks.md)
- [ADR 0015 - Layered sampling](0015-layered-sampling.md)
- [ADR 0016 - GPU memory smoke test](0016-gpu-memory-smoke-test.md)
- [ADR 0021 - Geometric augmentation smoke test](0021-augmentation-geometric-smoke-test.md)
- [ADR 0022 - Hypothesis reformulation after the pre-existing-augmentation discovery](0022-hypothesis-reformulation-post-augmentation-discovery.md)
- [ADR 0027 - Color augmentation at the sanity layer](0027-color-augmentation-sanity.md)
- [ADR 0033 - Consolidated current config, pre-validation](0033-consolidated-current-config.md)
- [ADR 0034 - First validation-tier run of the consolidated config](0034-first-validation-consolidated-config.md)
