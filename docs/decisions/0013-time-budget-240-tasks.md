# 0013 - Time budget projection for the 240-task real evaluation

**Status:** Informative (2026-09-07)

## Context

The official Kaggle notebook has a 12h execution limit, on 4x L4 GPUs,
against 240 real evaluation tasks (120 semi-private + 120 private, per
the user; the local public evaluation split mirrors the 120-task size,
confirmed by `ls data/ARC-AGI-2/data/evaluation | wc -l` = 120). All
timing so far comes from 8-task local samples on 1x RTX 4060 Ti (8GB
VRAM). This ADR projects whether the current, unmodified pipeline fits
the 12h budget. No cost-cutting change (fewer sampling attempts, a
per-task timeout, etc.) is made here.

## Real per-task timing already recorded

Three distinct measurements exist for the same 8-task evaluation sample,
because they used different code paths - they are not interchangeable
and are reported separately, not averaged together:

| Source | Code path | What it measures | Per-task avg |
|---|---|---|---|
| [ADR 0007](0007-raw-prediction-persistence.md), Context | `run_neural.py` / `solve_task` (production), pre-persistence run, not on disk | Full TTT + generation, textually recorded | ~15-20 min/task (~2.5h for 8 tasks) |
| `outputs/predictions/neural/evaluation/*.json` mtimes (post-ADR-0007 persisted re-run) | `run_neural.py` / `solve_task` (production) | TTT + self-consistency check that short-circuits on the *first* train pair (per [ADR 0009](0009-empty-candidate-diagnosis.md), self-consistency fails on pair 0 for all 8 tasks, so test-pair generation is skipped and it falls to the baseline) | ~7.1 min/task (7 measured inter-task deltas, sum 2979s / 7 = 425.6s) |
| `outputs/diagnostics/generation_counts/evaluation/*.json` mtimes (ADR 0009's instrumented run) | `run_generation_diagnostics.py`, deliberately does **not** short-circuit - samples every train *and* test pair in full | TTT + full per-pair sampling (up to 6 attempts/pair) regardless of outcome | ~27.4 min/task (7 measured inter-task deltas, sum 11486s / 7 = 1640.9s) |

The ~7.1 min/task production figure is fast **because accuracy is
currently near zero**: `_passes_self_consistency`
(`src/solvers/neural_solver.py:29-34`) returns `False` on the very first
train pair for every one of these 8 tasks, so `solve_task` never
generates predictions for the remaining train pairs or any test pair -
it falls straight to the symbolic baseline. This is not a genuine
performance margin; it is a byproduct of the empty-candidate problem
ADR 0009/0010 are investigating separately.

## Projection: 240 tasks, no parallelization

Multiplying each recorded rate by 240 tasks, single GPU, no changes:

| Rate used | 240-task total | vs. 12h budget |
|---|---|---|
| ~7.1 min/task (fast, short-circuit-dominated) | 1704 min = 28.4h | 2.4x over |
| ~15-20 min/task (ADR 0007, midpoint 17.5) | 4200 min = 70.0h | 5.8x over |
| ~27.4 min/task (full sampling, no short-circuit) | 6576 min = 109.6h | 9.1x over |

Under every recorded rate, unparallelized, the current pipeline does
**not** fit in 12h - the best case is still 2.4x over budget.

## Projection: 240 tasks, with parallelization

Explicit assumption used here (not validated): task-level parallelism
across Kaggle's 4x L4 GPUs, one task per GPU at a time, crediting only
the **GPU count** (4x) and nothing for L4 vs. RTX 4060 Ti per-GPU speed
differences (both are Ada Lovelace generation; L4 has 24GB VRAM against
the local 8GB, likely somewhat faster per-op, but that margin is left
uncredited here to stay conservative). This also assumes the 4-way split
has no orchestration overhead and no code exists yet in this project to
actually run it - that code would still need to be written.

| Rate used | 240-task total / 4 | vs. 12h budget |
|---|---|---|
| ~7.1 min/task | 7.1h | **Fits**, ~4.9h margin |
| ~15-20 min/task | 17.5h | 5.5h over |
| ~27.4 min/task | 27.4h | 15.4h over |

Only the fastest, short-circuit-dominated rate fits inside 12h, and only
under the optimistic 4x parallelization assumption above.

## The tension this raises

The one scenario that fits (7.1 min/task x 4-way parallel) is fast
*because* the model currently fails almost immediately on every task
(ADR 0009). If the parsing/self-consistency problem under investigation
in ADR 0010 gets fixed and more tasks start passing self-consistency,
`solve_task` will start generating full test-pair predictions instead of
short-circuiting, pushing the real rate toward the ~27.4 min/task figure
- which does **not** fit in 12h even with 4x parallelization (15.4h
over). Improving accuracy and staying inside the time budget are in
tension with the current architecture; they cannot be planned for
independently. This is a data point for the next joint decision, not a
choice made here.

## Not done in this ADR

No sampling-attempt reduction, no per-task timeout, no early-exit
tuning, and no multi-GPU orchestration code. These are candidate levers
for a joint decision once the accuracy-side findings (ADR 0009/0010) are
also on the table.

## References

- [ADR 0003 - Base model and fine-tuning strategy](0003-base-model-and-finetuning-strategy.md)
- [ADR 0007 - Raw prediction persistence](0007-raw-prediction-persistence.md) (source of the ~15-20 min/task, ~2.5h/8-task textual figure)
- [ADR 0009 - Empty-candidate diagnosis](0009-empty-candidate-diagnosis.md) (source of the self-consistency short-circuit behavior and the instrumented full-sampling run)
