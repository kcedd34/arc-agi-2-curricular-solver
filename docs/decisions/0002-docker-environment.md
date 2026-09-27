# 0002 - Docker environment

**Status:** Accepted, with a caveat about final hardware (see Context).
Local execution via Docker Desktop is superseded by
[ADR 0004](0004-wsl2-native-execution.md); the research on the official
Kaggle scoring environment below remains valid.

## Context

### ⚠️ Discrepancy found between initial assumption and official documentation

The initial project context assumed scoring hardware of "4x NVIDIA L4
GPU, 12h window". Research done for this ADR (2026-09-06) **does not
confirm these numbers**. What is officially documented today:

- **Accelerators available in Kaggle notebooks** (official starter kit,
  [docs.arcprize.org/arc-prize-2026](https://docs.arcprize.org/arc-prize-2026)):
  `cpu` (no GPU), `T4` (Nvidia T4 ×2, recommended default), `P100`
  (Nvidia P100, more memory), `RTX 6000` (`g4-standard-48`, **exclusive to
  the ARC-AGI-3 competition**, not ARC-AGI-2).
- The official competition page ([arcprize.org/competitions/2026/arc-agi-2](https://arcprize.org/competitions/2026/arc-agi-2))
  states verbatim: **"Hardware and compute limits will be announced with
  the competition launch"**, meaning the final limits for the private
  *scoring* environment have not been published yet.
- The previous edition (ARC Prize 2024) used **1x P100, 12h window, no
  internet**. It's reasonable to use this as an order-of-magnitude proxy
  until the official announcement, but it should not be treated as final.
- Confirmed (via [arcprize.org/competitions/2026](https://arcprize.org/competitions/2026)
  and the ARC-AGI-2 category page): submission deadline **2026-11-02**,
  winners announced **2026-12-04**, no internet access during evaluation
  ("no API-based systems like GPT/Claude/etc."), 2 predictions per test
  task, $700k in prizes (Progress $275k, Grand $275k, Bonus $150k for
  first to reach 85%).

**Project decision:** use T4/P100 (1 GPU) as the sizing assumption until
the official hardware announcement, since that's what is actually
documented today for Kaggle notebooks in this competition. Revisit this
ADR as soon as the official hardware announcement is out.

### Kaggle base image (confirmed via [Kaggle/docker-python](https://github.com/Kaggle/docker-python), `Dockerfile.tmpl`, 2026-09-06)

- The GPU image builds on top of
  `us-docker.pkg.dev/colab-images/public/runtime` (Google Colab's
  runtime), not a generic CUDA image.
- **Python 3.12** (`PACKAGE_PATH=/usr/local/lib/python3.12/dist-packages`).
- Package manager: `uv pip` (not plain pip).
- `torch`/`tensorflow`/`keras`/`jax` come frozen from the Colab runtime
  itself (version not explicitly pinned in `kaggle_requirements.txt`),
  then merged with additional Kaggle packages
  (`transformers>=5.0.0`, `torchtune`, `torchmetrics`, `torchinfo`,
  `torchcodec==0.11.0`, `scikit-learn` and variants, etc.).
- `pycuda` is only installed in the GPU variant.

## Decision

Build a local `docker/Dockerfile` that:

1. Uses **Python 3.12** as its base (via an `nvidia/cuda` image with
   Python 3.12, since the exact `colab-images/public/runtime` image is
   not publicly redistributable/buildable outside Kaggle).
2. Installs `torch` with CUDA support compatible with a local **8GB
   VRAM** GPU (CUDA 12.x build, no requirement for multiple GPUs).
3. Replicates the libraries relevant to the solver (`numpy`, `scipy`,
   `pandas`, `scikit-learn`, `transformers`, `torchmetrics`), pinning
   versions known to be compatible with Python 3.12, to reduce the risk
   of breakage when porting to Kaggle.
4. Does **not** try to replicate the Colab runtime bit-for-bit
   (impractical and not redistributable), the goal is *code behavior*
   parity (same Python version, same library APIs), not image parity.

## Consequences

- **What can be validated locally:** solver code correctness, DSL/model
  logic, evaluation harness, metrics against the public dataset, memory
  usage of a single process/GPU.
- **What CANNOT be validated locally:** real parallelism across multiple
  GPUs (should the final Kaggle hardware have more than one), absolute
  execution time under the official hour limit (not yet announced),
  exact Colab runtime behavior.
- Before final submission, revisit this ADR once the official Kaggle
  hardware is announced and adjust parallelism/batch size assumptions as
  needed.
- The local 8GB GPU is enough for light fine-tuning (LoRA) of small
  models, but larger models tested locally will need to be quantized or
  run in CPU mode to fit in VRAM, this is a development limitation, not
  a scoring one.

## Alternatives considered

| Alternative | Pros | Cons |
|---|---|---|
| `nvidia/cuda` image + Python 3.12 (chosen) | Locally buildable, full control over versions, close enough to the real runtime in terms of API | Not bit-for-bit identical to the Colab runtime |
| Try to extract/clone the exact Colab image | Perfect parity | Image is not publicly redistributable for local builds; infeasible |
| No-Docker environment (local venv) | Faster setup | Doesn't enforce Python/lib version parity with Kaggle; higher risk of "works here, breaks there" |

## References

- [docs.arcprize.org/arc-prize-2026](https://docs.arcprize.org/arc-prize-2026)
- [arcprize.org/competitions/2026/arc-agi-2](https://arcprize.org/competitions/2026/arc-agi-2)
- [github.com/Kaggle/docker-python](https://github.com/Kaggle/docker-python)
- [ADR 0001 - Solver approach selection](0001-solver-approach-selection.md)
