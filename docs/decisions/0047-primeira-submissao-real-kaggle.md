# 0047 - First real Kaggle submission (symbolic solver only)

Status: Informative (real submission made, ref 56256382; scored, publicScore 0.00, as expected)

## Context

ADR 0034 measured the full neural pipeline's real per-task cost at
269.92s, projecting about 18.0h for 240 tasks - 1.5x over the
unparallelized 12h Kaggle limit (ADR 0013), and multi-GPU
parallelization is deliberately deferred. ADR 0040 made the symbolic
solver the primary development priority, but ADR 0041-0046 established
its held-out coverage is 0/40 on two independent validation samples. No
real submission has ever been made to Kaggle in this project.

Given the neural pipeline cannot fit the time budget yet and the
symbolic solver's accuracy is already known to be near zero, the goal
of this first submission is explicitly not accuracy: it is to validate
that the real Kaggle environment works end to end (notebook execution,
input file discovery, `submission.json` format, no-internet execution,
total run time), using the cheapest, most mechanically reliable path
available - the symbolic solver, which needs no GPU and no model
weights.

### State check before starting (per explicit user instruction)

The request that started this session referred to a parallel Kaggle
compatibility effort (minimal notebook, MCP investigation, offline
packaging) as already partially done. A direct check of the repository
before any implementation found none of that:

- `notebooks/` was empty (no `.ipynb` file existed anywhere in the
  project tree).
- No ADR, no entry in `docs/progress.md`, and no line in this project's
  own memory records (`MEMORY.md` and its linked files) mentions a
  Kaggle notebook, an MCP investigation, or offline packaging work.
- No Kaggle MCP server is configured in this Claude Code installation
  (`claude mcp list` shows only three unrelated Google Workspace
  connectors: Drive, Gmail, Calendar).
- No Kaggle CLI credentials exist on this machine (`~/.kaggle` does not
  exist).
- The project directory itself is not a git repository (no `.git`), so
  there is no commit history to check for since-reverted work either.

Conclusion: nothing from that described effort exists in this
environment. Rather than guess whether it happened in a different
session/machine and was lost, or never actually happened, this is
recorded here so a future conversation does not re-search for phantom
prior work. Everything below was built from scratch in this session.

## Decision

Three new pieces, kept deliberately small per project convention (one
responsibility per file):

1. **`src/utils/kaggle_io.py`** (`load_challenges`): the official
   competition file combines every task into one JSON object
   (`task_id -> {"train": [...], "test": [...]}`), and its test pairs
   carry no `output` field - that is exactly what a submission predicts,
   unlike the local per-task-file dataset (`src/utils/task_loader.py`)
   where every pair has a known output. `load_challenges` reads that
   combined format into the existing `Task`/`Pair` types, using a fixed
   placeholder (`[[0]]`) for the test pairs' missing output field. That
   placeholder is never read on the solve/submission-build path: only
   `src.evaluation.harness.evaluate_solver` reads `Pair.output`, and that
   path is for scoring against known local answers, a case that
   structurally cannot arise for real competition test data.

2. **`src/evaluation/build_kaggle_submission.py`** (`build_and_write`):
   wires `load_challenges` to the existing, unmodified
   `src.solvers.baseline_solver.solve_task` and
   `src.evaluation.submission_format.build_submission`/
   `validate_submission`/`write_submission` (ADR 0006), timing the run
   and returning a small summary. Callable both as a local dry run and,
   with the real competition path, from inside a notebook - though the
   actual submission notebook (next item) does not import it, by design.

3. **`notebooks/kaggle_submission_symbolic.ipynb`**: the notebook meant
   to be uploaded to Kaggle. It inlines the same logic as the two
   modules above (geometric transforms, color mapping, the solver, the
   submission builder/validator, and the ADR 0011 fallback) as plain
   functions operating on dicts, rather than importing this repository.
   This is a deliberate trade-off: with no Kaggle MCP access and no
   Kaggle Dataset upload of this repo prepared, a self-contained
   notebook is the most robust option - it has zero dependency on
   attaching this project as a Dataset and zero pip installs, since
   every function it uses is standard-library Python. The notebook
   auto-discovers the competition's input path by walking
   `/kaggle/input` for a `*test_challenges.json` file (ADR 0006 already
   names this exact filename) instead of hardcoding a competition slug,
   and falls back to a local synthetic file so the same notebook can be
   smoke-tested outside Kaggle. It never calls the Kaggle submission
   API - the last cell only writes and summarizes `submission.json`,
   per explicit instruction not to trigger a real submission
   automatically.

### Local validation performed (no Kaggle access available in this session)

- `tests/test_kaggle_io.py` and `tests/test_build_kaggle_submission.py`
  (5 new tests) plus the existing `test_baseline_solver.py`/
  `test_submission_format.py`/`test_submission_fallback.py` all pass
  (25/25).
- `outputs/_diagnostics/dry_run_kaggle_submission.py` (throwaway,
  gitignored) took the full local 120-task evaluation split, stripped
  test outputs, wrote it as one combined file matching the official
  format exactly, and ran `build_and_write` end to end: 120/120 tasks
  solved and validated in 0.14s (about 1.2ms/task - no timing risk
  whatsoever, unlike the neural pipeline), zero exceptions,
  `validate_submission` passed. Informational accuracy on this
  synthetic run was 0/167 held-out test pairs, consistent with ADR
  0040-0046's already-known near-zero symbolic coverage - expected, not
  a defect in this pipeline.
- `outputs/_diagnostics/execute_kaggle_notebook_cells.py` (throwaway,
  gitignored) validated the notebook itself, since no
  jupyter/nbconvert/ipykernel is installed in this environment and
  installing new packages for a one-off check was judged out of scope:
  it extracts the notebook's 7 code cells in file order and `exec`s them
  in one namespace, the same order a real Kaggle kernel would run them.
  Result: all 7 cells ran without error against the same synthetic
  120-task file (via the notebook's own local fallback path), producing
  an identical valid `submission.json`. This checks the notebook's
  actual inlined code, not just the `src/` modules it mirrors.

### Kaggle MCP / remote execution

No Kaggle MCP server is configured in this Claude Code installation
(confirmed above), so committing or running the notebook remotely from
here is not possible in this session. The manual path is:

1. Open the ARC Prize 2026 competition page on Kaggle and create a new
   notebook (or upload `notebooks/kaggle_submission_symbolic.ipynb`
   directly via **File > Upload Notebook**).
2. Attach the competition's data under **Add Input** (this makes
   `/kaggle/input/.../*test_challenges.json` appear; no manual download
   needed and no internet access is required by the notebook itself).
3. Confirm the notebook's internet toggle is off (it needs none - pure
   standard-library Python).
4. Run all cells (**Run All**). Expected: a printed per-task time (well
   under a second total, going by the local dry run) and a final
   `submission.json` under `/kaggle/working/`.
5. Review the printed sanity summary (real-candidate vs. fallback pair
   counts) and the output file.
6. **Do not click Submit yet.** Per explicit instruction, that step
   needs the user's own confirmation first, since it consumes one of a
   limited number of daily submission attempts.

### Connectivity re-check (2026-09-15, same day, follow-up session)

A follow-up request in the same investigation asked to actually
configure Kaggle connectivity (MCP and/or classic CLI) and proceed
toward a real upload, on the stated premise that this had "already been
done before in this same conversation." Per explicit instruction, this
was re-verified from scratch rather than taken on faith, the same
discipline the original state check above used:

- `claude mcp list` showed the same three Google Workspace connectors as
  the original state check, still no `kaggle` entry - the earlier
  finding holds, nothing was lost or exists elsewhere.
- `claude mcp add --transport http kaggle https://www.kaggle.com/mcp`
  registered the server; `claude mcp list` now reports it as
  `Connected` at the transport level, but no Kaggle tools are exposed
  yet (checked directly) and no OAuth grant has happened. Completing
  that grant requires an interactive browser flow via `/mcp`, which
  only the user can run; this session is non-interactive for that
  purpose.
- `~/.kaggle/kaggle.json` (classic CLI credentials) does not exist, and
  the `kaggle` Python package is not installed. Per explicit user
  instruction, no credential file or token was created or requested on
  the user's behalf; generating a Legacy API token at
  kaggle.com/settings/api and placing it locally is left entirely to
  the user.

Net result: Kaggle connectivity is registered but not yet authenticated
by either path. Step 2 (notebook upload, attaching input, running on
Kaggle) is blocked on one of these two paths being completed by the
user; nothing beyond this connectivity check was attempted this pass.

### Real execution on Kaggle (2026-09-15, same day, after user configured the CLI)

The user generated a Legacy API token themselves (kaggle.com/settings/api)
and configured `~/.kaggle/kaggle.json` locally; `kaggle competitions list`
then worked and confirmed enrollment (`userHasEntered: true`) in
`arc-prize-2026-arc-agi-2`. The `kaggle` MCP server stayed registered but
unauthenticated (no OAuth grant); the classic CLI path was used instead
since it was already functional, and Kaggle's `kernels push`/`status`/
`output` commands cover the whole upload-run-download cycle without it.

Steps actually executed:

1. `kaggle competitions files -c arc-prize-2026-arc-agi-2` confirmed the
   real input filename (`arc-agi_test_challenges.json`, 1,015,295 bytes),
   matching what the notebook's auto-discovery already looks for.
2. `notebooks/kernel-metadata.json` was created (new, permanent, checked
   into the repo alongside the notebook it configures): `kernel_type:
   notebook`, `code_file: kaggle_submission_symbolic.ipynb`,
   `is_private: true`, `enable_gpu: false`, `enable_internet: false`
   (the competition's own requirement), `competition_sources:
   ["arc-prize-2026-arc-agi-2"]` (this is what makes
   `/kaggle/input/competitions/arc-prize-2026-arc-agi-2/...` appear at
   run time, no manual "Add Input" click needed).
3. `kaggle kernels push -p notebooks/` uploaded the notebook and
   triggered a real remote run at
   `https://www.kaggle.com/code/kcedd34/arc-agi-2-symbolic-submission-adr-0047`
   (auto-generated slug; a harmless title/slug-mismatch warning was
   printed, not an error).
4. `kaggle kernels status -k ...` polled every 10s; the run reached
   `KernelWorkerStatus.COMPLETE` on the third check (about 20-30s after
   push, most of it Kaggle's own kernel provisioning/queueing, not
   notebook execution time).
5. `kaggle kernels output -k ...` downloaded the real
   `submission.json` and the run log to
   `outputs/_diagnostics/kaggle_real_run/` (gitignored).

Real log output (`outputs/_diagnostics/kaggle_real_run/*.log`) confirms:

- Input found at
  `/kaggle/input/competitions/arc-prize-2026-arc-agi-2/arc-agi_test_challenges.json`,
  exactly the auto-discovery path the notebook was designed for, no
  hardcoded slug needed.
- **240 tasks / 259 test pairs** in the real competition test set - not
  120 like this project's local evaluation split, an important scale
  difference for any future timing extrapolation involving the real
  test set specifically.
- Solved and validated in **0.018s** (0.08ms/task); zero exceptions,
  matching the local dry run's zero-exception result at a different
  scale.
- **2/259 test pairs got a real symbolic candidate, 257/259 fell back**
  to the ADR 0011 safety net - consistent with the near-zero coverage
  already established on two independent local validation samples (ADR
  0040-0046), now confirmed on the real held-out competition test set
  itself, the first time this project has measured that directly.
- No internet activity of any kind was needed or attempted, consistent
  with `enable_internet: false` in the kernel metadata.

Local re-validation of the real output: the official
`arc-agi_test_challenges.json` was also downloaded locally
(`kaggle competitions download`) and both files were checked with this
project's own tooling, not just ad hoc inspection -
`src.utils.kaggle_io.load_challenges` plus
`src.evaluation.submission_format.validate_submission` against the real
240-task file and the real downloaded `submission.json`: **validates
cleanly, no `ValueError`, 240/240 tasks present**. This is the same
validator the local dry run used, now confirming the real Kaggle-run
output is format-correct, not just the local one.

**The "Submit to Competition" action was not clicked and no equivalent
CLI/MCP call (`kaggle competitions submit`) was made.** Per explicit
user instruction, that step is deliberately left for the user's own,
separate, explicit approval, since it consumes one of a limited number
of daily submission attempts. `submission.json` and the run log are
available under `outputs/_diagnostics/kaggle_real_run/` for review; the
kernel itself remains viewable at the URL above.

### Real submission to the competition (2026-09-15, same day, after explicit user approval)

The user reviewed the validated `submission.json` (see previous section)
and gave explicit approval in chat ("esta aprovado pode submeter") to
use one of the competition's limited daily submission attempts. Only
after receiving that approval was any submission call made.

The first attempt used the naive, generic Kaggle CLI command and
failed:

```
kaggle competitions submit -c arc-prize-2026-arc-agi-2 \
  -f outputs/_diagnostics/kaggle_real_run/submission.json -m "..."
```

Result: `400 Client Error: Bad Request`. Inspecting the raw response
body (`e.response.text`) revealed the real cause: `{"code":400,
"message":"Submission not allowed:  This competition only accepts
Submissions from Notebooks."}`. This is a **Code Competition**: direct
file-upload submission is not accepted at all, regardless of file
correctness. The correct API is `kaggle.api.competition_submit_code`,
which submits a specific, already-pushed-and-run kernel version (not a
raw file) as the competition entry. This is a permanent fact for any
future submission from this project, including a future neural-pipeline
one.

The corrected call, made once, right after finding the correct method
(`inspect.signature`/`inspect.getsource` used first to confirm its
signature before calling it for real):

```python
kaggle.api.competition_submit_code(
    file_name='submission.json',
    message='ADR 0047: first real submission, symbolic solver only '
             '(baseline geometric+color transforms), environment/'
             'pipeline validation, not an accuracy attempt',
    competition='arc-prize-2026-arc-agi-2',
    kernel='kcedd34/arc-agi-2-symbolic-submission-adr-0047',
    kernel_version=1,
)
```

Result: `{"message": "", "ref": 56256382}` - accepted by Kaggle.
Confirmed via `kaggle competitions submissions -c
arc-prize-2026-arc-agi-2`:

```
fileName          date                        description                                   status                     publicScore  privateScore
submission.json   2026-09-15 14:17:36.937000  ADR 0047: first real submission, symbolic...   SubmissionStatus.PENDING
```

A follow-up poll (6 checks, 20s apart) still showed
`SubmissionStatus.PENDING` with no score yet; Kaggle's scoring had not
completed as of that check. This is the project's **first real
submission ever made to the ARC Prize 2026 leaderboard** (ref
`56256382`), consuming one of a limited number of daily attempts, made
only after the user's own explicit, separate approval, exactly as
required.

### Score received (2026-09-15, same day, later check)

A later check of `kaggle competitions submissions -c
arc-prize-2026-arc-agi-2` showed the submission had finished scoring:

```
fileName,date,description,status,publicScore,privateScore
submission.json,2026-09-15 14:17:36.937000,...,SubmissionStatus.COMPLETE,0.00,
```

`status`: `SubmissionStatus.COMPLETE`. `publicScore`: **0.00**.
`privateScore`: not shown, consistent with Kaggle's usual practice of
withholding the private leaderboard score until the competition's
deadline rather than a pending/error state.

A public score of 0.00 is the expected result, not a defect: it matches
the near-zero symbolic-solver coverage already measured on two
independent local validation samples (ADR 0040-0046) and confirmed on
the real 240-task/259-pair competition test set itself (2/259 real
candidates, see above). This submission's stated goal was environment
validation, not accuracy, and that goal is now fully met: the complete
pipeline (build, push, run, download, submit) worked end to end on
Kaggle's real infrastructure and produced a real, scored leaderboard
entry.

## Consequences

- **A real, scored submission now exists** (ref 56256382,
  symbolic-solver-only, `SubmissionStatus.COMPLETE`, publicScore 0.00,
  privateScore withheld pending the competition deadline). The 0.00
  public score is the expected result, matching the near-zero symbolic
  coverage already established (ADR 0040-0046); this submission's real
  goal, Kaggle environment validation end to end, is fully achieved.
- This gives the project a real, tested, zero-dependency path to a
  Kaggle submission that does not require solving the neural pipeline's
  time-budget problem (ADR 0013/0034) or the symbolic solver's coverage
  problem (ADR 0040-0046) first - both stay exactly where they were.
- The notebook and the `src/` modules it mirrors (`grid_ops.py`,
  `color_mapping.py`, `baseline_solver.py`, `submission_format.py`,
  `submission_fallback.py`) are two independent copies of the same
  logic by design (see Decision, item 3). Any future change to the
  symbolic solver's logic must be ported to the notebook by hand; this
  ADR is the place that records that duplication so it is not mistaken
  for redundant/dead code later.
- `src/utils/kaggle_io.py` and `src/evaluation/build_kaggle_submission.py`
  are new, permanent, tested project modules (not throwaway), usable
  again for any future submission (e.g. once the neural pipeline fits
  the time budget) by swapping the solver passed to `build_submission`.
- The competition is a Code Competition: `kaggle competitions submit`
  (raw file upload) is rejected outright with a 400 error regardless of
  file correctness; only `kaggle.api.competition_submit_code`, which
  submits an already-pushed-and-run kernel version, is accepted. This
  governs any future submission from this project.
- The "parallel Kaggle compatibility effort" referenced at the start of
  this session is now confirmed to not exist in this repository,
  environment, or memory; future sessions should treat this ADR, not
  that reference, as the starting point for Kaggle submission work.

## Alternatives considered

| Alternative | Pros | Cons |
|---|---|---|
| Notebook imports this repo via a Kaggle Dataset upload of the source tree | No logic duplication, single source of truth | Requires a manual Dataset upload step and attaching it to the notebook before every run; no Kaggle MCP access in this session to automate or verify that step; adds a moving part to a submission whose whole point is minimizing risk of environment failure |
| Self-contained notebook inlining the same logic as plain functions (chosen) | Zero dependency beyond the competition's own input data; zero pip installs; works the moment the `.ipynb` is uploaded | Two copies of the same logic to keep in sync by hand; documented explicitly in Consequences so it is a known, deliberate trade-off |
| Skip local validation entirely and only test on Kaggle directly | Less work now | No Kaggle access available in this session to test on; would mean uploading untested code, exactly the failure mode this whole submission exists to avoid |
| Run the neural pipeline in a time-boxed/partial form instead of symbolic-only | Might get a non-zero real score | Contradicts this ADR's actual goal (environment validation, not accuracy) and reintroduces the exact 12h budget risk (ADR 0013/0034) this first submission is meant to sidestep |
| Trigger the real Kaggle submission automatically once local checks pass | Faster end-to-end | Explicit user instruction: submissions are a scarce daily resource and require human confirmation before use |

## References

- [ADR 0001 - Solver approach selection](0001-solver-approach-selection.md)
- [ADR 0006 - Submission format](0006-submission-format.md)
- [ADR 0011 - Submission safety net](0011-submission-safety-net.md)
- [ADR 0013 - Time budget for 240 tasks](0013-time-budget-240-tasks.md)
- [ADR 0034 - First validation-tier run of the consolidated config](0034-first-validation-consolidated-config.md)
- [ADR 0040 - Priority pivot: symbolic solver becomes primary](0040-pivot-prioridade-solver-simbolico.md)
- [ADR 0041 - Sizing the symbolic-solver expansion](0041-dimensionamento-solver-simbolico.md)
- [ADR 0046 - Second independent sample confirms the null pattern is not sample-specific](0046-segunda-amostra-cobertura-simbolica.md)
