# 0003 - Base model and fine-tuning/TTT strategy

**Status:** Accepted (2026-09-06)

## Context

[ADR 0001](0001-solver-approach-selection.md) decided that the solver's
core is a locally fine-tuned neural model + test-time training (TTT).
What remained was deciding: which base model, which fine-tuning strategy,
and how it fits the available hardware (local: 8GB VRAM; Kaggle:
T4x2/P100, 16GB per GPU, per
[ADR 0002](0002-docker-environment.md)).

Research into the state of the art documented by ARC Prize itself
(2026-09-06):

- **ARC Prize 2025, ARC-AGI-2 category, winner: NVARC (NVIDIA).**
  Used **Qwen3-4B** with **LoRA fine-tuning via the Unsloth framework**,
  TTT, and synthetic data generation (103k synthetic puzzles, expanded to
  3.2 million via augmentation). Result: **24% on the private set**, the
  best publicly documented number for ARC-AGI-2. Source:
  [github.com/1ytic/NVARC](https://github.com/1ytic/NVARC),
  [NVIDIA Technical Blog](https://developer.nvidia.com/blog/nvidia-kaggle-grandmasters-win-artificial-general-intelligence-competition/).
- In ensemble with Qwen3-4B, NVARC also used a **Tiny Recursive Model
  (TRM)**, a small recursive architecture with no pretrained LLM behind
  it, trained specifically for grids (see alternatives below).
- Documented smaller alternatives: OmniARC used Qwen2.5-0.5B-Instruct;
  MindsAI used a T5 model.
- ARC Prize 2024 (ARC-AGI-1 category, an easier benchmark): winner "the
  ARChitects" used NeMo-Minitron-8B + TTT, 53.5% on the private set, not
  directly comparable to ARC-AGI-2, which is harder by design.

## Decision

- **Base model:** Qwen3-4B.
- **Fine-tuning:** LoRA via the **Unsloth** framework (same choice as the
  2025 winning solution, optimizes LoRA to fit smaller GPUs and speeds
  up training).
- **Local environment (8GB VRAM):** load the model with 4-bit
  quantization (QLoRA) to fit available VRAM during
  development/testing.
- **Kaggle environment (T4x2/P100, 16GB per GPU):** re-evaluate whether
  4-bit quantization is still needed or whether higher precision
  (bf16/fp16) fits, a fine-tuning decision, not a blocker for starting
  development.
- **TTT:** quick weight adaptation (LoRA) per task, using the task's own
  training pairs at inference time, never an external API call (Golden
  Rule 4 in CLAUDE.md).
- **Out of scope for now:** large-scale synthetic data generation and
  ensembling with the Tiny Recursive Model. Both are recorded as possible
  future evolution (see Consequences), not part of the first
  implementation.

## Consequences

- New dependencies to add to the stack: `unsloth`, `peft`,
  `bitsandbytes`, `accelerate` (in addition to `torch`/`transformers`
  already anticipated in ADR 0002).
- Before writing code, the implementation needs to be broken down into
  explicit subtasks (CLAUDE.md rule): Qwen3-4B loading pipeline,
  formatting ARC tasks as prompts, LoRA/QLoRA configuration, per-task TTT
  loop, integration with the existing symbolic baseline as a fallback.
- Unsloth has installation instructions sensitive to the CUDA/PyTorch
  version, validate the local build before assuming the current
  Dockerfile (ADR 0002) works without adjustment.
- Open future evolution (not decided now, requires its own ADR if
  pursued): synthetic training data generation and ensembling with the
  Tiny Recursive Model, more fully replicating the NVARC solution.

## Alternatives considered

| Alternative | Pros | Cons |
|---|---|---|
| **Qwen3-4B + LoRA/Unsloth (chosen)** | Only path with real documented results on ARC-AGI-2 (24% private); mature HuggingFace/Unsloth ecosystem | Still needs QLoRA to fit 8GB local VRAM; higher fine-tuning cost than smaller models |
| Qwen2.5 0.5B-1.5B + TTT | Much faster per-task training/inference; useful if the Kaggle time budget turns out to be tight (not yet announced) | Likely lower accuracy ceiling; no documented result as strong as the 4B specifically on ARC-AGI-2 |
| Tiny Recursive Model (TRM) | Much lighter; doesn't depend on a pretrained LLM; part of the 2025 winning ensemble | No ready HuggingFace ecosystem, needs a from-scratch implementation; more experimental for a first iteration |
| NeMo-Minitron-8B / Llama-3-8B (2024 winner's line) | Larger model, more capacity | Validated on ARC-AGI-1 (easier), not on ARC-AGI-2; heavier for local 8GB VRAM |

## References

- [ADR 0001 - Solver approach selection](0001-solver-approach-selection.md)
- [ADR 0002 - Docker environment](0002-docker-environment.md)
- [github.com/1ytic/NVARC](https://github.com/1ytic/NVARC)
- [NVIDIA Technical Blog - NVIDIA Kaggle Grandmasters Win ARC Prize 2025](https://developer.nvidia.com/blog/nvidia-kaggle-grandmasters-win-artificial-general-intelligence-competition/)
