# 0020 - Next accuracy lever: data augmentation, not hyperparameter tuning

Status: Accepted

## Context

ADR 0018 found the neural solver's remaining bottleneck is content, not
parsing: the model copies the input through unchanged instead of
applying the task's transformation. ADR 0019 ran a `smoke`-layer
ablation (same 2 tasks) to check whether that behavior is under-training
(fixable by more TTT epochs or a larger LoRA rank) or insufficient
per-task signal (2-3 demonstration pairs, fixable only by adding more
training data per task).

ADR 0019's result, on the one pair that showed the copy-paste pattern
(`135a2760` train pair 0):

- `epochs_x2` (double TTT epochs) avoided a literal input copy and
  produced the only exact match in the whole diagnostic chain, but on
  the *training* pair itself, not the task's held-out test pair, which
  still scored `exact_match: no` for all three configs including
  `epochs_x2`.
- `lora_rank_x2` (double LoRA rank) showed no comparable effect,
  behaving like `baseline`.
- `epochs_x2` also cost noticeably more wall time per task (~245s for
  2 tasks vs. `lora_rank_x2`'s ~184s), scaling directly with epoch
  count, against an already tight per-task time budget (ADR 0013).

## Decision

**Deprioritize the hyperparameter axis (TTT epochs, LoRA rank) as the
main accuracy lever. Move to synthetic data augmentation as the next
content-side lever.**

Reasoning:

- A model reaching `exact_match` on a pair it was directly trained on,
  while still failing the task's held-out test pair, is the textbook
  signature of memorization/overfitting to the training examples, not
  of learning the underlying transformation. More epochs pushing
  further in that direction (better fit on seen pairs, no change on
  unseen ones) is the expected behavior of an already-converging model
  starved for training signal, not evidence that more epochs alone
  would fix generalization.
- This reasoning rests on a well-known failure mode (overfitting from
  too little training signal) plus one concrete empirical data point
  from ADR 0019 (a single train-pair exact match paired with a
  held-out-pair miss, on one task). It is not a statistically robust
  result, only two tasks and one signal-bearing pair were sampled, per
  Golden Rule 7 this alone cannot carry full confidence. The decision
  leans on the mechanism being well-understood, not on the sample size
  being large.
- Doubling LoRA rank showed no accuracy signal at all in ADR 0019, so
  there is no competing hyperparameter-axis result pulling toward
  continuing that line instead.
- Given ADR 0013's already-tight 12h/240-task time budget, spending
  further budget on an axis (more epochs) whose only measured effect so
  far is overfitting a seen example, at a direct wall-time cost, is a
  worse bet than an axis that targets the actual suspected cause
  (too few demonstration pairs per task).

**The hyperparameter axis is not permanently ruled out.** If data
augmentation does not resolve the content bottleneck (or resolves it
only partially), revisiting TTT epochs/LoRA rank, possibly combined
with augmentation rather than as an alternative to it, remains an open
option.

## Consequences

- No solver code changes from this ADR. `NeuralSolverConfig` keeps its
  current defaults (`ttt_num_epochs=3`, `lora_rank=16`,
  `lora_alpha=16`); ADR 0019's ablation tooling stays available if the
  hyperparameter axis is revisited later.
- Next planning step (separate from this ADR): design the data
  augmentation approach jointly with the user before implementing
  anything, covering at minimum: which per-task transformations to
  apply to generate synthetic demonstration pairs, how many synthetic
  examples per task, and how the added TTT cost per task interacts with
  the ADR 0013 time budget.
- CLAUDE.md Section 6 "Missing" item is updated to reflect this
  decision: the next lever is data augmentation, not hyperparameter
  tuning, with implementation still pending a joint design pass.

## Alternatives considered

- **Keep pushing the hyperparameter axis (e.g. epochs x4, epochs x8, or
  a combined epochs+rank config) before switching axes:** rejected for
  now, ADR 0019 already shows the one positive signal on this axis is
  consistent with overfitting, not generalization, and further epochs
  would only be expected to deepen that same effect while also costing
  more wall time per task.
- **Treat ADR 0019's evidence as too weak to decide anything and run a
  larger (`sanity`-layer) hyperparameter ablation before choosing:**
  rejected, the overfitting mechanism this decision leans on is
  well-established independent of sample size, and the time cost of a
  larger hyperparameter sample is better spent validating the
  augmentation approach instead, given the tight overall time budget.
- **Pursue ensembling with the symbolic baseline instead of data
  augmentation:** not rejected outright, but not chosen as the
  immediate next step, since ADR 0009's finding still holds that the
  symbolic baseline has no applicable transform for most sampled tasks
  in this domain, making it a weaker complement until the neural
  solver's own content accuracy improves.

## References

- [ADR 0009 - Empty-candidate diagnosis](0009-empty-candidate-diagnosis.md)
- [ADR 0013 - Time budget for 240 tasks](0013-time-budget-240-tasks.md)
- [ADR 0015 - Layered sampling](0015-layered-sampling.md)
- [ADR 0018 - Post-EOS-fix parsing-vs-content diagnosis](0018-post-eos-fix-parsing-vs-content-diagnosis.md)
- [ADR 0019 - Hyperparameter ablation on input-copying behavior](0019-hyperparameter-ablation-input-copying.md)
