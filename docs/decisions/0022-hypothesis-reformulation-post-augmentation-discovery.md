# 0022 - Hypothesis reformulation after the pre-existing-augmentation discovery

Status: Informative

## Context

ADR 0021's investigation found that geometric augmentation was already
active, unconditionally, in every diagnostic run since ADR 0009,
including the ADR 0019 hyperparameter ablation that ADR 0020's decision
was based on. ADR 0020 chose data augmentation as the next lever on the
premise that the pipeline had none yet; that premise was incorrect. This
ADR does not replace ADR 0020's decision (data augmentation over
hyperparameter tuning remains the chosen next step), it corrects the
reasoning behind it and records what ADR 0021's actual result implies,
now that the "before/after augmentation" framing no longer applies
cleanly.

This ADR does not implement anything. It is a reasoning correction plus
one new candidate hypothesis flagged for a future joint decision, per
the same Golden Rule 7 standard applied to every other informative ADR
in this chain.

## Decision

**1. The premise behind ADR 0020 needs correction, not the decision
itself.**

ADR 0020 reasoned that ADR 0019's one positive hyperparameter signal
(the `epochs_x2` train-pair exact match) was overfitting given "too few
demonstration pairs per task", implying more data (augmentation) was
the untried fix. In fact, 7-of-8 D4 geometric augmentation (up to 8x
the raw pairs) was already present during that exact ablation. The
"too few pairs" framing was correct in spirit (2-3 raw pairs is a small
signal) but understated: the model was already training on up to
7x-8x that many augmented pairs and still showed the copy-paste/
overfitting pattern ADR 0019 observed. This weakens, specifically, the
expectation that **more geometric augmentation of the same shape,
within the same single task, would resolve the content/generalization
bottleneck on its own** - that amount of data was already present
across ADR 0009-0020 without resolving it.

**2. ADR 0021 confirmed augmentation has real, demonstrated value, but
in a different place than assumed: output format reliability, not
(yet) confirmed content generalization.**

ADR 0021's `no_augmentation` vs. `geometric_full` (the corrected, full
8-element control this discovery made possible) comparison found:

- `no_augmentation` fails to parse any valid grid at all for 2 of 7
  pairs, producing runaway, structurally malformed output.
  `geometric_full` parses reliably almost everywhere. This is a real,
  newly demonstrated effect of augmentation on **format** during TTT.
- On the held-out test pairs specifically, `geometric_full` shows
  `num_copies_of_input: 0` on both (parsing succeeded on both), so the
  literal copy-input failure mode does not appear there in this sample.
  This is a genuine data point in favor of augmentation changing
  *something* about held-out behavior.
- However, `exact_match` is still "no" on every pair in both configs,
  including both held-out test pairs. Augmentation not producing a
  literal copy is not the same as augmentation producing the correct
  transformation. **Content/generalization success is still neither
  confirmed nor refuted** by this sample; it is a smaller, narrower
  claim than "augmentation fixes generalization".

**3. Candidate hypothesis for future evaluation (not implemented now):**
the real generalization bottleneck may not be *volume of augmentation
within a single task*, but the complete absence of a broader,
cross-task fine-tuning phase before per-task TTT. NVARC (the ARC Prize
2025 winning solution this project's ADR 0003 strategy is modeled on)
expanded its 103k-task training corpus to 3.2M examples and fine-tuned
across that whole corpus before any per-task TTT step. This project's
pipeline has never had an equivalent stage: every diagnostic so far,
augmented or not, trains a fresh LoRA adapter from the base checkpoint
on a single task's own (possibly augmented) pairs, with no exposure to
any other task's structure beforehand. If the bottleneck is that the
base model has no general prior over ARC-style transformations at all
(as opposed to too little per-task signal), then no amount of
within-task geometric augmentation would be expected to fix it, since
it only ever multiplies variations of the same one task's own examples.
This is a materially bigger change (a cross-task pretraining/fine-tuning
stage added to the architecture, not another augmentation multiplier)
and is recorded here only as a candidate for a future joint decision,
not implemented or scheduled.

## Consequences

- No code changes. `NeuralSolverConfig` defaults unchanged.
- ADR 0020's decision (data augmentation as the next lever, over
  hyperparameter tuning) stands; this ADR narrows what "augmentation"
  can be expected to deliver on its own (format reliability, demonstrated;
  content generalization, unresolved) and flags that the historical
  comparison baseline ADR 0019/0020 leaned on already included
  augmentation, so future comparisons should be read against
  `no_augmentation` (ADR 0021), not against the pre-ADR-0021 assumed
  "no augmentation" state, which never existed.
- CLAUDE.md Section 6 "Missing" item is updated to include the
  cross-task pretraining candidate hypothesis as an open item for a
  future joint decision, alongside the still-pending color augmentation
  design and production D4-variant count.
- The cross-task pretraining hypothesis (item 3) is not scheduled. It
  requires a joint decision given its scope (a new training stage, a
  much larger training corpus derived from the full ARC-AGI-2 training
  split, and a materially larger one-time compute cost) before any
  design or implementation work starts.

## Alternatives considered

- **Treat ADR 0021's held-out `num_copies_of_input: 0` result as
  sufficient evidence that augmentation solves generalization and
  proceed straight to picking a production variant count:** rejected,
  `exact_match` remaining "no" on every held-out pair means the model
  is still wrong, just wrong in a different way; conflating "not a
  literal copy" with "learned the transformation" would overstate this
  sample's evidence, against Golden Rule 7.
- **Reverse ADR 0020's decision back toward the hyperparameter axis,
  since its original premise was wrong:** rejected, the premise error
  (assuming augmentation was untried) does not invalidate the rest of
  ADR 0020's reasoning (the overfitting mechanism, the wall-time cost
  of more epochs, the lack of any hyperparameter-axis signal), and
  augmentation still separately demonstrated a real, positive effect
  (parsing reliability) in ADR 0021 that the hyperparameter axis has no
  equivalent result for.
- **Start designing or scoping the cross-task pretraining stage now,
  given how directly it addresses the discovery in this ADR:** rejected
  for this round, it is a materially larger architecture change than
  anything decided so far in this project and the user explicitly asked
  for it to be recorded as a candidate only, pending a joint decision
  once both findings from ADR 0021/0022 are considered together.

## References

- [ADR 0003 - Base model and fine-tuning strategy](0003-base-model-and-finetuning-strategy.md)
- [ADR 0009 - Empty-candidate diagnosis](0009-empty-candidate-diagnosis.md)
- [ADR 0013 - Time budget for 240 tasks](0013-time-budget-240-tasks.md)
- [ADR 0018 - Post-EOS-fix parsing-vs-content diagnosis](0018-post-eos-fix-parsing-vs-content-diagnosis.md)
- [ADR 0019 - Hyperparameter ablation on input-copying behavior](0019-hyperparameter-ablation-input-copying.md)
- [ADR 0020 - Next accuracy lever: data augmentation, not hyperparameter tuning](0020-lever-decision-data-augmentation.md)
- [ADR 0021 - Geometric augmentation smoke test](0021-augmentation-geometric-smoke-test.md)
