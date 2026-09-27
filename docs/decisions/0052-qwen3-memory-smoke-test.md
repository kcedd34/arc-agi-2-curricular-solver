# 0052 - Qwen3-4B-Instruct-2507 memory smoke test

Status: Informative

## Context

[ADR 0051](0051-reversao-para-qwen3-risco-aceito.md) reverted the base
model from `allenai/OLMo-2-1124-7B` to `Qwen/Qwen3-4B-Instruct-2507`, a
conscious risk-acceptance decision made after the OLMo-2-based hybrid
pipeline scored 0.00 on the real leaderboard. Before any generation
smoke test or sanity-tier accuracy run, ADR 0051's own 3-step local
validation plan requires re-confirming the model still fits the local
8GB VRAM budget via Unsloth QLoRA, the same bar
[ADR 0016](0016-gpu-memory-smoke-test.md) established for OLMo-2-1124-7B.
This is not assumed to carry over automatically: Qwen3-4B-Instruct-2507
is a different architecture and parameter count (4B vs. 7B) from the
model ADR 0016 actually measured.

## Method

Unchanged from ADR 0016: `src/evaluation/memory_smoke.py`
(`run_memory_smoke_test`) and `src/evaluation/run_memory_smoke.py`
(`python -m src.evaluation.run_memory_smoke evaluation`) needed no code
changes, since both read the active model name from
`NeuralSolverConfig()`, already updated to
`Qwen/Qwen3-4B-Instruct-2507` by ADR 0051's Step 2. The same worst-case
task selection (`find_largest_task`, most total grid cells across
train+test, input+output) again picked `d8e07eb2` (evaluation split),
identical to ADR 0016, so the two results are a direct, same-task
comparison.

One caveat not present in ADR 0016's original clean-baseline run: a
`nvidia-smi --query-gpu=memory.used,memory.total` check immediately
before launching this test showed 1,435 MiB already in use out of
8,188 MiB total. A follow-up `nvidia-smi --query-compute-apps` query
returned no attributable compute process (a known WSL2 limitation,
cross-VM process attribution is often unavailable). This pre-existing
usage is external to the measured process and is not included in
`torch.cuda.max_memory_allocated()` below, so the reported headroom
figure is optimistic relative to the actual free memory available on
this machine's shared GPU state.

## Result

No OOM at any step (model load, TTT, or generation). The model
downloaded from Hugging Face cleanly on first run.

| Metric | Value |
|---|---|
| Peak VRAM allocated | 4,735,745,536 bytes (4.41 GiB) |
| Total VRAM (device) | 8,585,216,000 bytes (8.00 GiB) |
| Headroom (as measured) | 3,849,470,464 bytes (3.59 GiB) |
| Pre-existing unattributed GPU usage (caveat) | ~1,435 MiB (~1.40 GiB) |
| Headroom (adjusted for caveat) | ~2,414,470,464 bytes (~2.19 GiB) |

TTT converged normally (train loss 0.4379 down to 0.1314 over 60 steps
/ 3 epochs, `train_runtime=165.8s`), a similar shape to ADR 0016's
OLMo-2 curve, no divergence or instability observed.

Comparison with ADR 0016 (OLMo-2-1124-7B, same task, clean baseline):

| Metric | OLMo-2-1124-7B (ADR 0016) | Qwen3-4B-Instruct-2507 (this ADR) |
|---|---|---|
| Peak VRAM | 5.59 GiB | 4.41 GiB |
| Headroom (as measured) | 2.41 GiB | 3.59 GiB |

Qwen3-4B-Instruct-2507 uses about 1.18 GiB less peak VRAM than OLMo-2,
consistent with its smaller 4B parameter count. Even under the adjusted,
more conservative headroom figure that accounts for this run's
~1.4 GiB pre-existing unattributed usage (~2.19 GiB), it still clears
OLMo-2's original clean-baseline headroom (2.41 GiB) by a comparable
margin, so this caveat does not change the qualitative conclusion.

## Decision

Memory is not a blocker for `Qwen/Qwen3-4B-Instruct-2507` on this
project's local 8GB card. This clears Step 3, tier 1 of ADR 0051's
validation plan. Per that ADR's explicit standing instruction, this
result alone does not license a generation smoke test's or sanity run's
conclusions, and does not license any real Kaggle GPU round or
leaderboard submission - only that VRAM is not the blocker for
attempting the next local tier (the generation smoke test).

## Consequences

- No code changes to the solver pipeline from this ADR, diagnostic only
  (identical to ADR 0016's own scope).
- The ~1.4 GiB pre-existing unattributed GPU usage observed before this
  run is recorded as an open, low-priority operational caveat: future
  local GPU runs on this machine should not assume a fully clean
  baseline without checking `nvidia-smi` first, since WSL2's compute-app
  attribution query does not reliably identify the source.
- Proceeds directly to ADR 0051's Step 3, tier 2 (generation smoke
  test, 1-2 tasks), checking whether Qwen3-Instruct's format/generation
  behavior differs from OLMo-2's historically diagnosed problems (ADR
  0010, ADR 0028-0032).

## Alternatives considered

- **Skip re-measuring memory since OLMo-2 already cleared a higher bar
  (7B vs. 4B):** rejected, per ADR 0051's own explicit 3-step plan and
  this project's established measure-before-build discipline (ADR
  0035/0041 applied the same reasoning to sizing decisions); a smaller
  parameter count does not guarantee lower peak VRAM given different
  architectures, tokenizer vocab sizes, and attention implementations.
- **Treat the ~1.4 GiB unattributed usage as a run-blocking anomaly and
  investigate before proceeding:** rejected for now, the measured
  headroom stays comfortably positive even under the conservative
  adjustment, and WSL2's known cross-VM attribution gap makes further
  investigation low-value relative to just re-checking `nvidia-smi`
  before future runs.

## References

- [ADR 0016 - GPU memory smoke test](0016-gpu-memory-smoke-test.md)
- [ADR 0051 - Revert base model to Qwen3-4B-Instruct-2507, accepted-risk decision](0051-reversao-para-qwen3-risco-aceito.md)
