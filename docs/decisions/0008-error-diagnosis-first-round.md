# 0008 - Error diagnosis, first round

**Status:** Informative (2026-09-06)

## Context

The first neural solver run on an 8-task/11-test-pair sample of the
evaluation split scored 0/11 (0%, see `docs/progress.md`, 2026-09-06
entry for `run_neural.py evaluation 8`). That number alone doesn't say
*why* it failed. This ADR records a post-hoc diagnostic pass, built in
`src/evaluation/pair_diagnostics.py` and `error_classifier.py`
(`build_error_report`, `run_error_diagnostics.py`), re-run against the
same 8 tasks with raw predictions persisted via ADR 0007's
`predictions_dir` so this exact report can be reproduced without
re-running the solver.

This ADR does not decide anything. It only records what the diagnostic
found, for the next joint decision on which improvement lever to pursue
(synthetic/augmented training data, LoRA hyperparameter tuning, or
ensembling).

## Report

| Task | Pair | Dimension match | Per-cell accuracy | Error class |
|---|---|---|---|---|
| 0934a4d8 | 0 | no | n/a | shape/count |
| 135a2760 | 0 | no | n/a | not classifiable |
| 136b0064 | 0 | no | n/a | shape/count |
| 13e47133 | 0 | no | n/a | not classifiable |
| 13e47133 | 1 | no | n/a | not classifiable |
| 142ca369 | 0 | no | n/a | not classifiable |
| 142ca369 | 1 | no | n/a | not classifiable |
| 16b78196 | 0 | no | n/a | not classifiable |
| 16de56c4 | 0 | no | n/a | not classifiable |
| 16de56c4 | 1 | no | n/a | not classifiable |
| 1818057f | 0 | no | n/a | not classifiable |

Persisted raw predictions (`outputs/predictions/neural/evaluation/`)
show every one of the 11 test pairs got zero candidate grids (`[[]]` or
`[[], []]` depending on the task's test-pair count), not merely
wrong-shaped ones - both the neural solver's generation/self-consistency
step and the baseline fallback produced nothing usable for any pair in
this sample.

## Dominant pattern observed

Dimension match is `no` and per-cell accuracy is `n/a` for all 11/11
pairs, because no candidate grid was produced at all, not because a
produced grid had the wrong shape or wrong cells. This is a generation
failure, not an accuracy problem in the usual sense. Of the 8 tasks, 6
are "not classifiable" by the train-pair heuristics (no clean color,
symmetry/rotation, or shape/count signal fits), and the other 2 show a
shape/count signal; no task in this sample showed a color or
symmetry/rotation signal alone, and none showed `combination`. The
sample is small (8 tasks) and skewed toward harder-to-classify
transformations, so this is a first read, not a general claim about the
full evaluation split.

## Next step (not decided here)

Per the standing instruction, no improvement lever is chosen in this
ADR. The finding to bring to the joint decision: the immediate blocker
observed here is candidates never surviving to output at all (self-consistency
filtering the neural solver's output, baseline finding no applicable
transform), before any question of *which* transform class the model
struggles with.

## References

- [ADR 0003 - Base model and fine-tuning strategy](0003-base-model-and-finetuning-strategy.md)
- [ADR 0007 - Raw prediction persistence](0007-raw-prediction-persistence.md) (made this report reproducible without re-running the solver)
