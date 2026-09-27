# Neural line (paused): setup and usage

Moved here verbatim from the root README on 2026-09-27 (ADR 0112). The neural line (ADR 0001-0060) is paused, not retracted; the root README now covers the curricular solver.

Solver for the ARC Prize 2026 competition (ARC-AGI-2 category, Kaggle).
Architecture decisions: [docs/decisions/](docs/decisions/). Key terms:
[docs/glossary.md](docs/glossary.md).

## Requirements

- **Windows with WSL2** (`Ubuntu-22.04` or similar) for GPU-backed work
  (neural solver, LoRA/TTT). See [ADR 0004](docs/decisions/0004-wsl2-native-execution.md):
  local execution runs natively inside WSL2, no Docker.
- Python ≥3.8 works for the symbolic baseline/tests (no GPU needed).
  Python 3.12 (inside WSL2) is required for the neural solver, for
  parity with the Kaggle runtime, see [ADR 0002](docs/decisions/0002-docker-environment.md).
- A local NVIDIA GPU with a driver that supports WSL2 GPU passthrough
  (no extra Linux driver install needed, Windows' driver is used
  directly inside WSL2).

## Local setup (symbolic baseline, no GPU)

Works on any Python ≥3.8, on Windows or inside WSL2:

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## WSL2 setup (neural solver, GPU)

1. Open a WSL2 terminal (`Ubuntu-22.04`). Install Python 3.12 via the
   `deadsnakes` PPA (not shipped by default on Ubuntu 22.04):

   ```bash
   sudo add-apt-repository -y ppa:deadsnakes/ppa
   sudo apt-get update -qq
   sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
   python3.12 --version
   ```

2. From the project root (e.g. `/mnt/d/Projetos/kaggle_contest` if the
   repo lives on a Windows drive), create a project-local virtual
   environment and install dependencies:

   ```bash
   python3.12 -m venv .venv312
   .venv312/bin/pip install --upgrade pip
   .venv312/bin/pip install -r requirements.txt
   ```

3. Verify GPU access from Python (no need for the `nvidia-smi` CLI,
   WSL2 exposes the GPU to CUDA directly through the Windows driver):

   ```bash
   .venv312/bin/python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
   ```

**Note on Unsloth (Qwen3-4B-Instruct-2507 fine-tuning, [ADR 0003](docs/decisions/0003-base-model-and-finetuning-strategy.md)/[ADR 0051](docs/decisions/0051-reversao-para-qwen3-risco-aceito.md)):**
the package is sensitive to the exact CUDA/PyTorch version. Before
installing, check the official install matrix at https://docs.unsloth.ai
and adjust `requirements.txt` if needed, don't assume the current pin
works in every environment without validating the install.

## Public dataset

Already included in `data/ARC-AGI-2/` (gitignored, don't version it).
To re-download from scratch:

```bash
git clone --depth 1 https://github.com/arcprize/ARC-AGI-2.git data/ARC-AGI-2
```

Structure: `data/ARC-AGI-2/data/training/*.json` (1000 tasks) and
`data/ARC-AGI-2/data/evaluation/*.json` (120 tasks, with output revealed
to allow local scoring).

## Run the tests

```bash
python -m pytest tests/ -v
```

## Run the evaluation harness against the public dataset

```bash
python -m src.evaluation.run_baseline evaluation   # or: training
```

Prints `test_pairs_total`, `test_pairs_correct`, and `accuracy`, a local
replica of the official metric (2 predictions per test input, exact
match). Every relevant run's result must be logged in
[docs/progress.md](docs/progress.md).

Each run also saves the raw predicted grids (not just the score) to
`outputs/predictions/{baseline,neural}/{split}/{task_id}.json`, gitignored,
reusable by later analyses without re-running the solver, see
[ADR 0007](docs/decisions/0007-raw-prediction-persistence.md).

## Running the neural solver

Requires the WSL2 setup above (Python 3.12, `.venv312/`, GPU-enabled
`torch`). From inside WSL2, at the project root:

```bash
.venv312/bin/python -m src.evaluation.run_neural evaluation   # or: training
```

An optional second argument either limits the run to the first N tasks
in the split (sorted by task id), or names a sampling layer (`smoke`,
`sanity`, `validation`, see [ADR 0015](docs/decisions/0015-layered-sampling.md)),
useful given the per-task TTT+generation cost. `smoke`/`sanity` results
never justify a policy/ADR decision on their own, only `validation`
does (Golden Rule 7):

```bash
.venv312/bin/python -m src.evaluation.run_neural evaluation 8        # raw limit
.venv312/bin/python -m src.evaluation.run_neural evaluation sanity   # tiered layer
```

Same output format as `run_baseline` above. The first run downloads
Qwen3-4B-Instruct-2507 (ADR 0051) from Hugging Face (several GB); expect
that download to dominate the first run's time. `solve_task` (see
[src/solvers/neural_solver.py](src/solvers/neural_solver.py)) attaches a
fresh LoRA adapter per task, fine-tunes it on that task's own (augmented)
train pairs (TTT, [ADR 0003](docs/decisions/0003-base-model-and-finetuning-strategy.md)),
and falls back to the symbolic baseline
([ADR 0001](docs/decisions/0001-solver-approach-selection.md)) whenever
the fine-tuned model fails a self-consistency check against its own
training pairs.

## Building the Kaggle submission file

`src/evaluation/submission_format.py` builds and validates
`submission.json` in the exact format the competition requires (one
`attempt_1`/`attempt_2` pair per test input, every `task_id` from the
input file present, see [ADR 0006](docs/decisions/0006-submission-format.md)):

```python
from src.evaluation.submission_format import build_submission, validate_submission, write_submission

submission = build_submission(solve_task, tasks)
validate_submission(submission, tasks)   # raises ValueError on any format problem
write_submission(submission, Path("submission.json"))
```

### Building from the official Kaggle challenges format

The snippet above uses this project's local per-task-file dataset. The
real competition instead provides one combined JSON file
(`arc-agi_test_challenges.json`, `task_id -> {"train": [...], "test":
[...]}`, test pairs with no `output`). `src/utils/kaggle_io.py` and
`src/evaluation/build_kaggle_submission.py` bridge that format to the
same submission builder (see
[ADR 0047](docs/decisions/0047-primeira-submissao-real-kaggle.md)):

```bash
python -m src.evaluation.build_kaggle_submission path/to/arc-agi_test_challenges.json --output submission.json
```

`notebooks/kaggle_submission_symbolic.ipynb` is the self-contained
notebook meant for upload to Kaggle (no repo import, no pip installs,
symbolic solver only, GPU-free). It never calls the Kaggle submission
API; running it only produces `submission.json` for review.

### Pushing and running the notebook on real Kaggle

Requires the Kaggle CLI (`pip install kaggle`) and `~/.kaggle/kaggle.json`
(generate a Legacy API token at kaggle.com/settings/api, this project
never generates or stores that token for you). `notebooks/kernel-metadata.json`
configures the push: `competition_sources` attaches the competition's
data as `/kaggle/input/...` automatically, and `enable_internet: false`
matches the competition's own no-internet rule.

**Always run the undefined-name check before any push.** The notebook
is self-contained (no `src/` import, see ADR 0047), so every cell must
be kept manually in sync; `ast.parse` alone only validates syntax, it
does not catch a name used but never imported/defined in an earlier
cell. This exact gap let a missing `StoppingCriteriaList` import through
an `ast.parse`-only check straight to a real, GPU-quota-consuming Kaggle
run (ADR 0049's "Fourth round attempt, notebook import bug found"). This
check exercises the same shared-namespace, top-to-bottom cell execution
the real Kaggle kernel uses, but statically (no GPU, no `unsloth`
required):

```bash
python -m src.evaluation.run_notebook_name_check
```

Exit code 0 and "OK: no undefined names found" means it is safe to push.
Any other output names the offending cell and must be fixed first.

```bash
kaggle kernels push -p notebooks/                                    # uploads + runs remotely
kaggle kernels status -k <username>/<kernel-slug>                    # poll until COMPLETE
kaggle kernels output -k <username>/<kernel-slug> -p some/local/dir  # download submission.json + log
```

This push/run/download cycle never calls the submission API itself -
that step is always a separate, explicit, manual decision (see
[ADR 0047](docs/decisions/0047-primeira-submissao-real-kaggle.md)),
since it spends one of a limited number of daily submission attempts.
Note this competition is a **Code Competition**: the generic
`kaggle competitions submit` (raw file upload) is rejected outright with
a 400 error; a real submission requires
`kaggle.api.competition_submit_code(kernel=..., kernel_version=...)`,
pointing at an already-pushed-and-run kernel version, which is what ADR
0047 used for the project's first real submission (ref 56256382,
publicScore 0.00, the expected result for the symbolic-solver-only
baseline).

## Licensing

- Code released by winners of this competition is licensed CC BY 4.0.
- The ARC-AGI-2 dataset is licensed Apache 2.0.
- Development uses the dataset from the ARC Prize Foundation's public
  GitHub repository (see "Public dataset" above) under that license, not
  Kaggle's competition-specific Data tab, see
  [ADR 0005](docs/decisions/0005-ai-assistant-usage-in-development.md).

## Structure

```
src/
├── solvers/
│   ├── baseline_solver.py   # trivial symbolic baseline
│   ├── neural_solver.py     # Qwen3-4B-Instruct-2507 + LoRA/TTT, falls back to the baseline
│   └── neural/              # grid<->text, prompt building, config, model
│                             # loading, LoRA setup, TTT trainer, generation
├── evaluation/   # local evaluation harness, metrics, submission.json builder
└── utils/        # task loading, grid operations
tests/            # unit tests, mirror src/
docs/
├── decisions/    # ADRs
├── glossary.md
└── progress.md
```
