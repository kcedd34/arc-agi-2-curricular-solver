# 0050 - Static undefined-name check for the self-contained Kaggle notebook

Status: Accepted, implemented, and verified locally against the real notebook.

## Context

ADR 0049's "Fourth round attempt, notebook import bug found" section
documents a real Kaggle GPU round that produced zero valid circuit-
breaker evidence: every one of the 6 sampled tasks crashed with
`NameError: name 'StoppingCriteriaList' is not defined` immediately
after TTT finished, before generating a single token. Root cause was a
notebook-only missing import in Part C's circuit-breaker cell
(`StoppingCriteria` was imported, `StoppingCriteriaList` was not, even
though the generation cell needs it). This is the second occurrence of
the exact same drift class in the same Part C cell: ADR 0032's
reactivation note already found and fixed one prior instance (the
per-attempt conditional decode-escalation logic never having been
ported into Part C at all). Both times, the notebook's pre-push
structural check (`ast.parse` on every cell, see ADR 0049's
consolidation update) passed cleanly, because `ast.parse` only
validates syntax, it does not resolve names, so it cannot catch a name
that is used but never imported or defined anywhere in the notebook.

This drift risk is structural, not incidental: the notebook is
deliberately self-contained (ADR 0047, no `src/` import, since no
Kaggle MCP server or Dataset-based repo upload is configured), so every
change to `src/solvers/neural/*` that should also apply to the
notebook's Part C must be manually re-ported, with no import mechanism
to catch a forgotten name. Each real verification round consumes the
notebook's scarce, shared weekly Kaggle GPU quota, so a bug this cheap
to catch locally, caught only after a real GPU push, is a costly
process gap.

Two candidate approaches were given for a stronger, still fully local
check:

1. Run `pyflakes` (or an equivalent linter) over the notebook's code,
   flagging undefined names.
2. Extend `outputs/_diagnostics/execute_kaggle_notebook_cells.py`, an
   existing gitignored, throwaway `exec`-with-stubs script (ADR 0047)
   that runs all notebook code cells sequentially in one namespace, to
   run automatically before every notebook commit/push.

## Decision

**Chose option 1: a pyflakes-based static undefined-name check**
(`src/evaluation/notebook_name_check.py`), run via a new CLI entry
point, `python -m src.evaluation.run_notebook_name_check`.

Design:

- `src/evaluation/notebook_cells.py` (`extract_code_cells`) parses the
  notebook's raw `.ipynb` JSON and returns only code-cell sources, in
  execution order, skipping markdown cells.
- `src/evaluation/notebook_name_check.py` (`concatenate_cells`) joins
  all code cells into one synthetic source blob, in cell order,
  recording each cell's 1-based starting line in the combined source.
  This mirrors the real Kaggle execution model: all cells run
  top-to-bottom in one shared namespace, so a name imported in an
  earlier cell and used in a later one is valid and must not be
  flagged; checking cells independently would produce false positives
  for exactly this pattern (e.g. an import in cell 1, used in cell 3).
- `find_undefined_names` runs `pyflakes.checker.Checker` against the
  concatenated source's AST and filters `checker.messages` down to
  `pyflakes.messages.UndefinedName` instances, the exact bug class this
  ADR targets (pyflakes also reports other categories, e.g. unused
  imports, that are not relevant here and are not surfaced).
- Each flagged issue is mapped back from a global line number to its
  originating notebook cell index, so the CLI output is directly
  actionable ("cell 16, line 634: undefined name 'StoppingCriteriaList'")
  instead of a raw line number in a blob the user never sees.
- `src/evaluation/run_notebook_name_check.py` is the CLI entry point:
  exit code 0 and "OK: no undefined names found" on success, exit code
  1 with one line per issue otherwise. Defaults to
  `notebooks/kaggle_submission_symbolic.ipynb` but takes an explicit
  path for testing.

**Why option 1 over option 2:** pyflakes is pure static analysis, it
needs no GPU, no `unsloth`, and no model-loading code to run, so it
works in any environment (including plain host Python, no WSL2/GPU
required) and runs in well under a second. Extending the exec-with-
stubs script to run automatically would require stubbing the entire
GPU-dependent import chain (`unsloth`, `torch`, model loading) well
enough that Part B/C execute without a real accelerator, which is
substantially more implementation and maintenance surface for the same
one bug class this ADR targets (a name used but never imported or
defined). The exec-based approach remains valuable for a different
purpose, catching runtime-only failures that only surface once code
actually executes, but is not needed for this specific, narrower gap.

## Consequences

- `pyflakes>=3.2` added to `requirements.txt` (installed and confirmed
  working in the project's real WSL2 `.venv312` environment,
  `pyflakes-3.4.0`).
- New tests: `tests/test_notebook_cells.py` (2 tests: code-cell
  filtering/ordering, empty-notebook handling) and
  `tests/test_notebook_name_check.py` (6 tests, including a permanent
  regression test built from the exact `StoppingCriteriaList` bug
  shape, and a regression guard that runs the real check against the
  real `notebooks/kaggle_submission_symbolic.ipynb`, so this ADR's fix
  reappearing again would fail the suite, not just a manual notebook
  push).
- **Empirically confirmed against the real notebook, as explicitly
  requested:** running `python -m src.evaluation.run_notebook_name_check`
  against the current, already-locally-fixed notebook prints "OK: no
  undefined names found in kaggle_submission_symbolic.ipynb" (exit code
  0). A deliberately-reverted temporary copy (`StoppingCriteriaList`
  removed from the import, everything else unchanged, kept outside the
  repo as a scratch file, not committed) was checked separately and
  correctly flagged: `cell 16, line 634: undefined name
  'StoppingCriteriaList'`, reproducing the exact real Kaggle failure
  from ADR 0049's fourth round. This confirms the check would have
  caught that bug before it reached a real, GPU-quota-consuming Kaggle
  push.
- `README.md`'s "Pushing and running the notebook on real Kaggle"
  section now documents this check as a mandatory pre-push step, with
  the exact command and what success/failure output looks like, placed
  immediately before the existing `kaggle kernels push` instructions.
- This check does not replace the existing `ast.parse` structural
  check (still useful for catching plain syntax errors) or the
  exec-with-stubs script (still useful for a full runtime smoke test
  when GPU/`unsloth` stubs are worth maintaining for some other
  purpose); it closes specifically the used-but-never-imported/defined
  name gap that both of those miss.
- Does not, by itself, unblock or approve a new real Kaggle push. A
  genuine round 4 (confirming the circuit breaker's real behavior on
  `264363fd` and the rest of the calibration sample) still requires the
  user's own separate, explicit approval, per the standing instruction
  restated in ADR 0049.
- **Python 3.8 compatibility bug found and fixed post-implementation:**
  the project's own README states Python >=3.8 works for the symbolic
  baseline/tests (the neural line needs 3.12/WSL2, but this notebook
  check is pure static analysis with no GPU dependency, so it must also
  run under 3.8). The initial implementation of
  `src/evaluation/notebook_cells.py` and
  `src/evaluation/notebook_name_check.py` used builtin generic type
  hints (`list[str]`, `tuple[str, list[int]]`), which require Python
  3.9+ and raise `TypeError: 'type' object is not subscriptable` at
  import time under 3.8, exactly matching the rest of the codebase's
  established `typing.List`/`typing.Tuple` convention (checked against
  e.g. `src/evaluation/task_ordering.py`). This was only caught because
  the repository's automated Stop-hook verification runs the full suite
  on native Windows Python 3.8, where it failed collection for both new
  test files; the earlier "verified locally" claim above had only been
  checked against WSL2's Python 3.12 venv, missing this gap. Fixed by
  switching both files to `from typing import List, Tuple`; the fix was
  then confirmed against both real environments: 8/8 new tests pass on
  native Windows Python 3.8 (275 passed/1 skipped for the full suite,
  no collection errors) and on WSL2's Python 3.12 `.venv312` (8/8
  passing, unchanged from before the fix).

## Alternatives considered

| Alternative | Pros | Cons |
|---|---|---|
| Extend the exec-with-stubs script (`execute_kaggle_notebook_cells.py`) to run automatically pre-push | Also catches runtime-only failures beyond undefined names | Needs a GPU/unsloth/torch stub layer to run without real hardware, much larger scope for the one bug class actually being targeted |
| Do nothing beyond the existing `ast.parse` check | No new dependency or code | Already proven insufficient twice on this exact bug class (ADR 0032's original fix, ADR 0049's fourth-round bug), at the cost of real Kaggle GPU quota both times |
| Import notebook Part C code from `src/` instead of keeping it self-contained, eliminating the drift source entirely | Removes the root cause, not just a symptom | Contradicts ADR 0047's explicit self-contained design (no Kaggle MCP/Dataset-based repo upload configured); a larger redesign, out of scope for this ADR |

## References

- [ADR 0032 - Per-attempt conditional no_repeat_ngram_size mitigation](0032-per-attempt-conditional-ngram-mitigation.md)
- [ADR 0047 - First real Kaggle submission (symbolic solver only)](0047-primeira-submissao-real-kaggle.md)
- [ADR 0049 - Time-budgeted hybrid symbolic+neural submission pipeline](0049-pipeline-hibrido-orcamento-tempo.md)
