# ARC-AGI-2 curricular solver (ARC Prize 2026)

A CPU-only, model-free symbolic solver for ARC-AGI-2, built by curricular learning, plus
the full record of what did and did not work. The official Kaggle score of the submitted
solver is **0.83** (ref 56552321, [ADR 0104](docs/decisions/0104-submissao-real-do-solver-curricular.md)).
The technical line is closed ([ADR 0112](docs/decisions/0112-encerramento-da-linha-tecnica-rodada-23.md)):
an oracle measurement showed that only 10 of the 233 ARC-AGI-2-exclusive training tasks
(4.3%) are expressible by the solver's representation, and 9 of those were taught by hand.

Read first: the [Writeup](docs/writeup/solution_writeup_draft.md). Index of decisions:
[docs/decisions/README.md](docs/decisions/README.md). Mechanism catalogue:
[docs/curriculum/arc2-mechanisms.md](docs/curriculum/arc2-mechanisms.md). Round-by-round
records: [docs/curriculum/rounds/](docs/curriculum/rounds/). Glossary:
[docs/glossary.md](docs/glossary.md).

## Requirements

- Python 3.12 (3.10+ works for the solver and tests). Linux, macOS, WSL2 or Windows.
- `numpy` and the standard library are all the curricular solver imports at run time.
  `pytest` for the tests. No GPU, no internet, no model.
- The ARC-AGI-2 dataset (Apache 2.0), cloned into `data/ARC-AGI-2/` (not versioned).

## Reproduce

```bash
python -m venv .venv && . .venv/bin/activate
pip install numpy pytest
git clone --depth 1 https://github.com/arcprize/ARC-AGI-2.git data/ARC-AGI-2

python -m pytest tests -q                 # full suite (about 1000 tests)
python -m src.curriculum.cli validate     # schema and regression checks against the saved state
```

Expected: all tests green except one known failure of the paused neural line
(`tests/test_cross_task_pretraining.py::test_pretrain_shared_adapter_changes_model_weights`,
which needs torch and a GPU); `validate` reports 0 regressions. Every diagnostic command
writes its full detail to a file under `outputs/` and prints at most about 15 lines.

## Solve and evaluate

```bash
python -m src.curriculum.cli next                 # next unsolved curricular-pool task id
python -m src.curriculum.cli check <task_id>      # desk-check a task, state unchanged
python -m src.curriculum.cli probe                # held-out probe pool checkpoint
```

Build the submission file from an official-format challenges file (same command the Kaggle
notebook runs, one process per task, hard per-task timeout, global wall budget):

```bash
python -m src.curriculum.submission.build <challenges.json> --output submission.json --workers 4
```

The Kaggle notebook is generated, never edited by hand:

```bash
python notebooks/curricular/build_notebook.py
```

It embeds the exact `src/curriculum` tree as a base64 zip, so Kaggle runs the code the
tests cover. Pushing a kernel to Kaggle is a manual step, by the decider only.

## Frozen baseline

The submitted notebook, `kernel-metadata.json`, `build_notebook.py` and the submission
output are frozen by SHA-256 in `docs/curriculum/frozen-baseline.json`, and
`tests/curriculum/test_frozen_baseline_hashes.py` fails if any of them changes. Any new
work must leave these files untouched.

## Repository map

```
src/curriculum/      solver: spec/ (declarative vocabulary), library/, search/, perception/,
                     discovery/ (generated properties), submission/, desk_check/, verification/
src/curriculum/oracle/         Round 23 ceiling measurement (diagnostic only, never imported by the solver)
src/curriculum/program_probe/  Round 24 local-model program viability probe (diagnostic only)
tests/               mirrors src/ (tests/curriculum/...)
docs/writeup/        the Writeup
docs/decisions/      ADRs, index in README.md (one line per ADR)
docs/curriculum/     rules (BOOTSTRAP.md), catalogue, rounds/, handsolved/, learning-curve.md, progress.md
docs/history/        archived drafts and the pre-restart CLAUDE.md
docs/neural-line.md  setup and usage of the paused neural line (ADR 0001-0060)
notebooks/curricular/ generated Kaggle notebook and its metadata
```

## The paused neural line

The first line (OLMo-2 then Qwen3-4B with LoRA and test-time training, plus a symbolic
fallback; three real submissions, all 0.00) is paused, not retracted. Its setup (WSL2, GPU,
Unsloth) and commands are in [docs/neural-line.md](docs/neural-line.md). The curricular
solver does not depend on it.

## Licensing

- Code and documentation: **CC BY 4.0** (see [LICENSE](LICENSE)), per the ARC Prize 2026
  open-source requirement.
- The ARC-AGI-2 dataset is licensed Apache 2.0 by the ARC Prize Foundation and is not
  redistributed here (cloned separately, see Requirements above).
- Files derived from the dataset (the frozen submission output grids) remain Apache 2.0,
  matching the dataset's own license; see [NOTICE.md](NOTICE.md) for the exact scope.
