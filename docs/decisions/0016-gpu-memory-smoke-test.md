# 0016 - GPU memory smoke test

Status: Informative

## Context

The Unsloth ~5GB VRAM estimate for QLoRA fine-tuning of a 7B model is a
generic figure. It does not by itself validate this project's specific
setup: ARC-AGI-2 grids reach 30x30, the training prompt concatenates
every demonstration pair for the task in one context, and this project
does real per-task TTT (forward+backward), not just inference, plus
multiple sampled generations per prediction. Before running any larger
evaluation with `allenai/OLMo-2-1124-7B` (the OSAID-compliant model from
ADR 0014, combined with the EOS fix from ADR 0010), the worst-case single
task was smoke-tested in isolation to surface any out-of-memory failure
where its cause is unambiguous, rather than inside a larger run.

"Worst case" is defined as the evaluation-split task with the most total
grid cells across all train+test pairs (input+output), since the TTT
prompt holds all of a task's demonstrations in one context - a new
`src/evaluation/worst_case_task.py` (`find_largest_task`) selects it.

## Method

New `src/evaluation/memory_smoke.py` (`run_memory_smoke_test`) runs, on
the selected task, model load, TTT (`train_on_task`), and generation
(`generate_with_counts`) across all train+test pairs, tracking
`torch.cuda.max_memory_allocated()` throughout and catching
`torch.cuda.OutOfMemoryError` separately at each of the three steps so a
failure's exact location is unambiguous. New
`src/evaluation/run_memory_smoke.py` is the CLI entry point
(`python -m src.evaluation.run_memory_smoke [split]`), persisting the
result JSON under `outputs/diagnostics/memory_smoke_test/`.

Selected task: `d8e07eb2` (evaluation split), the largest by total cell
count.

## Result

No OOM at any step (model load, TTT, or generation).

| Metric | Value |
|---|---|
| Peak VRAM allocated | 5,997,069,824 bytes (5.59 GiB) |
| Total VRAM (device) | 8,585,216,000 bytes (8.00 GiB) |
| Headroom | 2,588,146,176 bytes (2.41 GiB) |

TTT converged normally on this task (train loss 1.24 down to 0.68 over
54 steps / 3 epochs, ~157s), consistent with the pattern already
observed on other tasks in `docs/progress.md`.

## Decision

The generic ~5GB estimate holds closely enough for this project's actual
worst-case task (5.59 GiB peak measured), with a comfortable ~2.4 GiB
margin on the 8GB card. No mitigation (context reduction, fewer
simultaneous samples, more aggressive gradient checkpointing, lower LoRA
rank) is needed or applied. This clears GPU memory as a blocker for
proceeding to a `sanity`-layer evaluation run (8 tasks, per
[ADR 0015](0015-layered-sampling.md)/Golden Rule 7) to confirm the
combined ADR 0014 (model) + ADR 0010 (EOS fix) changes work together
before any `validation`-layer run.

## Consequences

- No code changes to the solver pipeline from this ADR, diagnostic only.
- If a future change increases per-task context further (e.g. more
  demonstrations, longer generation budget, larger batch), this smoke
  test should be re-run rather than assumed to still hold, headroom is
  comfortable but not enormous (~30% of total VRAM).
- Per Golden Rule 7, this smoke-test result alone does not license a
  larger `validation`-layer run or any accuracy conclusion, only that
  memory is not the blocker for attempting one.

## Alternatives considered

- **Run the full evaluation split directly and rely on aggregate
  failure to surface OOM:** rejected, an OOM inside a large multi-task
  run is harder to attribute to a specific task/step, exactly the
  ambiguity this isolated smoke test avoids.
- **Pick the task with the largest single grid instead of the largest
  total cell count across all pairs:** rejected, the TTT prompt holds
  every demonstration pair in one context, so total cells across pairs
  is the figure that actually drives context length and memory, not any
  single pair's grid.

## References

- [ADR 0010 - Raw generation inspection](0010-raw-generation-inspection.md)
- [ADR 0014 - OSAID-compliant base model](0014-osaid-compliant-base-model.md)
- [ADR 0015 - Layered sampling](0015-layered-sampling.md)
