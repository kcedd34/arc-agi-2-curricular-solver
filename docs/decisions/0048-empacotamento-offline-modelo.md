# 0048 - Offline packaging of the neural model for Kaggle (OLMo-2-1124-7B + Unsloth stack)

Status: Accepted (validated end to end on real Kaggle infrastructure, zero network calls)

## Context

ADR 0046 resumed the neural line as the priority for accuracy gains. The
neural pipeline needs `allenai/OLMo-2-1124-7B` (ADR 0014) plus Unsloth,
bitsandbytes, peft, unsloth_zoo, trl, and xformers, none of which are
preinstalled on Kaggle's base notebook image, and Kaggle competition
kernels for this competition run with `enable_internet: false`
(confirmed already in ADR 0047). Before any time-budgeted hybrid
symbolic+neural pipeline (Part 2, next) can be built, the model and its
dependencies must be loadable and runnable on Kaggle with zero network
access - "a validação crítica antes de qualquer coisa mais complexa,"
per explicit user framing. This ADR covers that blocking prerequisite
only: packaging, upload, and a real no-internet validation run. It does
not implement the hybrid pipeline itself.

## Decision

### 1. Kaggle Models vs. Kaggle Datasets

Kaggle offers two attachment mechanisms for large binary artifacts:
"Kaggle Models" (`model_sources` in `kernel-metadata.json`) and "Kaggle
Datasets" (`dataset_sources`). Kaggle Datasets was chosen because the
classic `kaggle kernels push` CLI has a known bug where `model_sources`
entries in `kernel-metadata.json` are silently ignored on push
(`Kaggle/kaggle-api` GitHub issue #643) - the model would simply not be
attached to the kernel with no error raised, a much worse failure mode
than an upfront limitation. Kaggle Datasets has no equivalent bug and
supports the same size/privacy requirements, so both the model weights
and the dependency wheels are packaged as private Kaggle Datasets.

### 2. Real environment diagnostic before packaging

Before downloading anything, a minimal diagnostic notebook
(`notebooks/offline_model_diagnostic/offline_model_diagnostic.ipynb`)
was pushed and run for real on Kaggle (internet enabled, no model
attached) to measure the actual target environment rather than assume
it:

- GPU: **2x Tesla T4**, 14.56 GiB VRAM each (confirmed again during the
  final validation run below).
- `torch 2.10.0+cu128`, matching the local WSL2 dev environment exactly
  - no torch/CUDA build mismatch risk.
- Of the required stack, five packages are missing from the base image
  and must be shipped as wheels: `unsloth`, `unsloth_zoo`,
  `bitsandbytes`, `trl`, `xformers`. `torch`, `transformers`,
  `accelerate`, `peft`, `triton`, and `safetensors` are already present
  at compatible versions.

### 3. Wheelhouse dataset (dependency wheels)

The five missing packages were downloaded locally (`pip download
--no-deps`, matching the target platform) into
`notebooks/offline_wheelhouse/` and uploaded as a private Kaggle
Dataset, `kcedd34/arc-agi2-offline-wheelhouse-adr0048` (~126MB, 5
`.whl` files: `unsloth-2026.9.2`, `unsloth_zoo-2026.9.1`,
`bitsandbytes-0.50.2`, `trl-0.24.0`, `xformers-0.0.35`). `--no-deps` is
deliberate: the base image already has compatible versions of every
transitive dependency (torch, transformers, accelerate, peft, triton,
safetensors per the diagnostic above), and letting pip resolve
dependencies normally would require network access, defeating the
point.

### 4. Pre-quantized model dataset

Rather than shipping the 28GB fp32 OLMo-2-1124-7B checkpoint and
quantizing at load time on Kaggle, the model was quantized to 4-bit
(nf4) locally once via Unsloth (`FastLanguageModel.from_pretrained(...,
load_in_4bit=True)` then `model.save_pretrained()`/
`tokenizer.save_pretrained()`,
`outputs/_diagnostics/quantize_and_save_olmo_4bit.py`), shrinking it
from 28GB to **4.7GB**. This is uploaded as a second private Kaggle
Dataset, `kcedd34/arc-agi2-olmo2-7b-4bit-adr0048`, containing
`config.json`, `generation_config.json`, `model.safetensors` (~4.99GB),
`tokenizer.json`, `tokenizer_config.json`. Pre-quantizing once locally
avoids repeating the quantization step (and its dependency on the full
28GB fp32 weights) inside every future Kaggle kernel run.

### 5. Validation notebook and the real mount-path failure

`notebooks/offline_model_validation/` (`kernel-metadata.json`,
`enable_internet: false`, `enable_gpu: true`, both datasets attached
via `dataset_sources`) runs five checks in order: offline `pip install
--no-index --no-deps --find-links <wheelhouse> ...`, a direct check
that internet is unreachable, importing all five packages, loading the
model via `FastLanguageModel.from_pretrained` from the attached dataset
path, and one `model.generate` call.

The first two real runs (kernel versions 1 and 2) failed at the pip
install step: `WARNING: Location '/kaggle/input/<slug>' is ignored: it
is either a non-existing path or lacks a specific scheme`. This was not
a dataset-readiness or attachment problem (both datasets showed
`status: ready` and matched the exact refs in `dataset_sources`) - a
diagnostic cell added in version 2 revealed the real cause: **Kaggle
does not mount private datasets directly at `/kaggle/input/<slug>/`**.
The actual real-run mount structure was:

```
/kaggle/input/datasets/<owner>/<dataset-slug>/...
```

i.e. one extra `datasets/<owner>/` level of nesting versus the
commonly assumed `/kaggle/input/<slug>/` path. This is a genuine,
previously undocumented (in this project) Kaggle operational detail,
not a bug in the packaging itself. The notebook was fixed to resolve
both dataset paths by walking `/kaggle/input` and matching a keyword
(`wheelhouse`, `olmo2`) rather than hardcoding the mount path, and
re-pushed as kernel version 3.

### 6. Real validation result (kernel version 3, `KernelWorkerStatus.COMPLETE`)

All five checks passed for real, on Kaggle's actual infrastructure,
with `enable_internet: false`:

- Diagnostic cell confirmed the real mount tree:
  `/kaggle/input/datasets/kcedd34/arc-agi2-offline-wheelhouse-adr0048/`
  and `.../arc-agi2-olmo2-7b-4bit-adr0048/`, each containing exactly
  the expected files.
- `pip install --no-index --no-deps --find-links <wheelhouse> unsloth
  unsloth_zoo bitsandbytes trl xformers` returned exit code 0,
  installing all five packages from the local wheel files with zero
  network access.
- The explicit internet-reachability check confirmed `https://huggingface.co`
  is unreachable (`URLError: <urlopen error [Errno -3] Temporary
  failure in name resolution>`), proving `enable_internet: false` is
  actually enforced, not just configured.
- All five packages imported successfully with their real installed
  versions (`unsloth 2026.9.2`, `unsloth_zoo 2026.9.1`, `bitsandbytes
  0.50.2`, `trl 0.24.0`, `xformers 0.0.35`).
- `FastLanguageModel.from_pretrained(model_name=MODEL_DIR,
  load_in_4bit=True)` loaded the 4-bit checkpoint directly from the
  mounted dataset path with `HF_HUB_OFFLINE=1`/`TRANSFORMERS_OFFLINE=1`
  set, no Hub access attempted. Real hardware confirmed again at load
  time: 2x Tesla T4, 14.39-14.44 GiB budget each, ~4.5 GiB of weights
  split across both GPUs.
- `model.generate(**inputs, max_new_tokens=16)` produced valid decoded
  text with no exception:
  `'Input:\n0 0\n0 0\n\nOutput:\n0 0\n\n\nInput:\n0 0\n0 0\n\nOutput:\n'`
  - a real, well-formed (if untrained-for-the-task) completion, proving
  the full load -> inference path works offline end to end. Content
  quality is irrelevant here; this is a plumbing check, not an accuracy
  check.

Total wall time for the full notebook (pip install through generation):
about 154s, dominated by Unsloth's one-time compilation/patching pass
(~62-131s) rather than the model load itself.

## Consequences

- The blocking prerequisite for Part 2 (time-budgeted hybrid pipeline)
  is now satisfied: the neural pipeline's model and full dependency
  stack are confirmed loadable and runnable on real Kaggle
  infrastructure with `enable_internet: false`, matching the
  competition's actual constraint.
- Two new permanent private Kaggle Datasets exist and are reusable by
  any future kernel: `kcedd34/arc-agi2-offline-wheelhouse-adr0048`
  (~126MB, 5 wheels) and `kcedd34/arc-agi2-olmo2-7b-4bit-adr0048`
  (4.7GB, pre-quantized weights+tokenizer). Any future Kaggle kernel
  needing this stack should attach both via `dataset_sources` and
  resolve their mount paths by walking `/kaggle/input` (per item 5),
  not by hardcoding `/kaggle/input/<slug>/`.
- **New operational fact for this project, applies to every future
  Kaggle kernel using `dataset_sources`:** private datasets mount at
  `/kaggle/input/datasets/<owner>/<dataset-slug>/`, not
  `/kaggle/input/<dataset-slug>/`. Any future notebook attaching a
  dataset (this one or a new one) must resolve the path dynamically
  (e.g. `os.walk`) rather than hardcode the shallow path, or it will
  fail identically to kernel versions 1-2 here.
- Confirmed the `model_sources`/CLI push bug (issue #643) by choosing
  to avoid it entirely rather than reproduce it; if a future session
  needs Kaggle Models specifically (e.g. for public model sharing),
  that bug should be re-checked against the CLI version in use at the
  time, since it may since have been fixed upstream.
- Local operational lessons carried forward for any future scripted
  packaging work: running a script directly
  (`python some/nested/script.py`) puts the script's own directory on
  `sys.path[0]`, not the project root, breaking `from src...` imports
  even after `cd`-ing to the project root first - prefix with
  `PYTHONPATH=<project_root>` or invoke via `python -m`. Also, this
  project's `Write`-tool path restriction blocks writing outside
  `D:\Projetos\kaggle_contest`; any file that must live elsewhere (e.g.
  WSL `/tmp` scratch files) must be created via shell redirection
  instead.
- `notebooks/offline_model_validation/` stays in the repo as a
  reusable, real, no-internet smoke test for this exact model+
  dependency combination; re-run it after any change to the wheelhouse
  or model dataset contents before trusting a larger hybrid-pipeline
  kernel run.

## Alternatives considered

| Alternative | Pros | Cons |
|---|---|---|
| Kaggle Models (`model_sources`) instead of Datasets | Purpose-built for model weights, separate versioning UI | Classic CLI push silently ignores `model_sources` (issue #643) - a silent failure is worse than Datasets' extra path-nesting quirk |
| Ship fp32 weights (28GB) and quantize at kernel start | No local quantization step, single source of truth | 28GB upload/attach is far slower and costlier than 4.7GB; repeats the quantization cost on every kernel run for no benefit, since the quantized result is deterministic given the same base checkpoint |
| Hardcode `/kaggle/input/<slug>/` paths (as first attempted) | Simpler code | Empirically wrong on this Kaggle image (real mount is one level deeper under `datasets/<owner>/`); caused two real failed kernel runs before being diagnosed |
| Bundle all five missing wheels plus their full dependency closures (`pip download` without `--no-deps`) | Fully self-contained, no reliance on base-image versions matching | Much larger dataset for no measured benefit, since the diagnostic notebook already confirmed the base image has compatible `torch`/`transformers`/`accelerate`/`peft`/`triton`/`safetensors` |

## References

- [ADR 0013 - Time budget for 240 tasks](0013-time-budget-240-tasks.md)
- [ADR 0014 - OSAID-compliant base model](0014-osaid-compliant-base-model.md)
- [ADR 0033 - Consolidated current config](0033-consolidated-current-config.md)
- [ADR 0034 - First validation-tier run of the consolidated config](0034-first-validation-consolidated-config.md)
- [ADR 0046 - Second independent sample confirms the null pattern is not sample-specific](0046-segunda-amostra-cobertura-simbolica.md)
- [ADR 0047 - First real Kaggle submission (symbolic solver only)](0047-primeira-submissao-real-kaggle.md)
