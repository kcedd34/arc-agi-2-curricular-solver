# 0004 - WSL2-native execution instead of Docker Desktop

**Status:** Accepted (supersedes the local-execution part of
[ADR 0002](0002-docker-environment.md))

## Context

ADR 0002 decided to run all local GPU-heavy work (model loading, LoRA,
TTT, generation) inside a Docker image built from `docker/Dockerfile`,
using Docker Desktop on Windows as the runtime.

While starting the neural solver implementation, this was tried in
practice: Docker Desktop was started to validate GPU passthrough
(`docker run --gpus all ... nvidia-smi`) before building the project
image. The user judged Docker Desktop too heavy and slow for daily
development ("muito pesado e lento, vai nos atrasar") and asked to stop
using it immediately, moving all local execution to command-line-driven
WSL2 instead.

Facts checked before accepting this change:

- Docker Desktop on Windows already runs on top of WSL2 internally (a
  hidden `docker-desktop` distro). Removing Docker Desktop does not
  remove WSL2, it removes an extra heavy layer (background service, UI,
  its own VM management) on top of it.
- The existing `Ubuntu-22.04` WSL2 distro has working GPU passthrough
  without Docker: the Windows NVIDIA driver exposes `/dev/dxg` and
  `libcuda.so.1` (via `/usr/lib/wsl/lib`, resolved by `ldconfig`)
  directly inside the distro. The `nvidia-smi` CLI binary itself was
  simply not installed (no `nvidia-utils` package), which is cosmetic,
  not a functional GPU blocker, once a CUDA-enabled `torch` build is
  installed.
- Python 3.12 (the version ADR 0002 wanted for Kaggle-runtime parity)
  is installed directly in `Ubuntu-22.04` via the `deadsnakes` PPA,
  giving the same version parity ADR 0002 wanted, without a container.

## Decision

Local execution moves from "Docker Desktop + `docker/Dockerfile`" to
"native WSL2, command-line only":

1. All local development and solver runs happen inside the existing
   `Ubuntu-22.04` WSL2 distro, driven from the command line (`wsl -e
   ...` or a WSL-integrated terminal), never through Docker Desktop.
2. Python 3.12 is installed directly in that distro (`deadsnakes` PPA),
   in a project-local virtual environment (`.venv312/`), instead of a
   container image.
3. Project dependencies (`requirements.txt`, including `torch`,
   `transformers`, `peft`, `bitsandbytes`, `accelerate`, `unsloth`) are
   installed into that venv with `pip`, matching the CUDA build
   available for the local RTX 4060 Ti (8GB VRAM) instead of a
   Dockerfile-pinned build.
4. GPU access is verified directly from Python
   (`torch.cuda.is_available()`), since `nvidia-smi` is not installed
   and is not required.
5. `docker/Dockerfile` is kept in the repository as reference for a
   possible future containerized packaging step (e.g. final submission
   packaging), but it is not part of the day-to-day workflow anymore and
   is not required to reproduce this project locally.

ADR 0002's research on the official Kaggle scoring environment (base
image, Python version, package set, hardware caveat) remains valid and
unchanged, only the *local development* execution mechanism changes.

## Consequences

- **Faster local iteration:** no Docker Desktop startup cost, no image
  build/rebuild cycle for every dependency change, `pip install` directly
  in the venv is enough.
- **Lower isolation:** no container boundary between the project's
  Python environment and the rest of the WSL2 distro. Acceptable
  trade-off given this is a single-developer local setup, not a shared
  or production environment.
- **Reproducibility now depends on `requirements.txt` + documented OS
  packages** (Python 3.12 via `deadsnakes`) instead of a single
  buildable image. README.md must keep the exact WSL2 setup commands
  up to date (Golden Rule 2) so the environment stays reproducible from
  documentation alone.
- **`docker/Dockerfile` is no longer validated as part of normal
  development.** If it drifts out of date, that is expected; it should
  only be revisited if a containerized packaging need re-emerges (e.g.
  for the eventual Kaggle submission format, once official requirements
  are published).

## Alternatives considered

| Alternative | Pros | Cons |
|---|---|---|
| WSL2-native, command-line only (chosen) | Fast iteration, GPU passthrough already confirmed working, matches Python 3.12 parity goal without a container | Less isolation than a container |
| Keep Docker Desktop (ADR 0002 as-is) | Stronger isolation, single reproducible image | Explicitly rejected by the user for being too heavy/slow for daily development |
| Docker Engine inside WSL2 without Docker Desktop (no GUI/background service) | Keeps containerization, drops the heaviest Windows-side component | Still adds a build/run layer the user asked to remove entirely; not requested |
