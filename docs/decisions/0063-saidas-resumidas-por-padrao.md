# 0063 - Summarized-by-default CLI/diagnostic output (RN-CUR-32)

Status: Accepted (2026-09-21)

## Context

Per the governing "Prompt - Retomada apos /clear (tarefa 2) com
correcao estrutural de contexto", every CLI command and diagnostic
script under the curricular restart must print at most a short
(~15-line) status summary to the terminal, persisting full detail to a
file instead. This exists because full desk-check reports, search logs
(one line per enumerated hypothesis), and validation reports were
growing large enough to flood a session's own context when read back
via tool output, working directly against RN-CUR-30's requirement that
acceptance rely on real, fresh-process CLI execution (a command whose
output is unusable to read is a command nobody will actually run for
real).

Per RN-CUR-27, this is an implementation-level design decision
(module/function shape, output format), not one requiring prior
decisor consultation; it is recorded here with Status Accepted per that
rule's own text.

## Decision

### Shared helper

A single new module, `src/curriculum/cli_output.py`, centralizes the
pattern instead of repeating it ad hoc across six call sites:

- `write_detail(text: str, path: Path) -> Path` - creates parent
  directories as needed and writes `text` to `path`, returning the
  path unchanged, so callers can pass it straight into the summary.
- `print_summary(lines: List[str], detail_path: Path) -> None` -
  prints at most `MAX_SUMMARY_LINES - 1` lines (`MAX_SUMMARY_LINES =
  15`, leaving one line for the trailing `Full detail: <path>` line),
  then that trailing line.

Chosen over inlining `print(...)`/file-write pairs in each `cmd_*`
function: every affected surface needs the exact same two steps (write
full detail, print a bounded summary plus the path), so a shared helper
is a direct application of RN-CUR-27's own "small, single-responsibility
files" convention rather than six near-duplicate blocks.

### 15-line cap

Chosen as a round number comfortably below a typical terminal's visible
scrollback for one command, while still leaving room for 3-5 status
lines plus the path line on every affected command (the actual summaries
implemented range from 3 to 5 lines, well under the cap). No `--verbose`
escape hatch was added: the governing prompt explicitly states an
optional verbose flag "must never be used in the normal flow," so
omitting it entirely avoids a code path that would sit permanently
unused and untested.

### Affected surfaces (6)

`src/curriculum/cli.py`'s five subcommands, plus the search diagnostic
script's `__main__` block:

| Command | Full detail written to | Terminal summary |
|---|---|---|
| `check` | `outputs/curriculum/desk-check-reports/<task_id>-check.txt` | task id, status, verified-candidate count |
| `solve` | `outputs/curriculum/desk-check-reports/<task_id>-solve.txt` | task id, status, verified-candidate count, solved-marker line if applicable |
| `desk-check-persist` | the existing `docs/curriculum/desk-checks/<task_id>.md` (no new file; this command already persisted full detail, only its terminal print changed) | task id, status, persisted-candidate count |
| `validate` | `outputs/curriculum/validation-report.txt` | schema-error count, regression count, VALID/INVALID |
| `probe` | the existing `outputs/curriculum/state.json` (no new file; the checkpoint was already persisted there) | checkpoint date, exact-match fraction, accuracy, solved count |
| `search.diagnostics` (`__main__`) | `outputs/curriculum/search-log/<task_id>.txt` | task id, total enumerated, verified count, discarded count, final status |

`format_search_log`'s full per-hypothesis "Verified candidates:" list
stays unmodified inside the persisted file; only the terminal print
changed. `cmd_next` was left untouched (a single-line print, already
well under the cap, and not named in the governing prompt's target
list).

### Four additional operating rules

Beyond the code change itself, the governing prompt names four standing
rules for how this session (and future ones) interact with the now-large
output files, so the RN-CUR-32 discipline is not defeated by simply
reading the full file back into context after it's written:

1. Read only a search log's count headers (e.g. `head -n 20`), never
   its full per-hypothesis list.
2. Read only a desk check's `.md` summary, never its underlying `.json`
   artifact.
3. Refactor library files one at a time, preferring `grep -n` to locate
   a function before opening the file around it, rather than reading an
   entire large file to make a small change.
4. Delegate heavy reads or long-running analysis to a subagent that
   returns a short summary, rather than pulling raw detail directly into
   the main session's context.

## Consequences

- Every RN-CUR-30 real-execution acceptance check from here on produces
  terminal output short enough to read directly, while the full detail
  needed for a genuine desk check or search-log review stays on disk at
  a predictable path.
- `tests/curriculum/test_cli.py` was updated for the new output shape:
  `test_cmd_solve_does_not_write_state_when_not_solved`'s stub now sets
  `task_id`/`verified` on its `run_desk_check` fake (the new summary
  logic reads both), and
  `test_cmd_validate_reports_valid_for_a_clean_state` now asserts
  `"VALID"` is an exact printed line rather than a string suffix (a
  naive substring/suffix check would false-pass against `"INVALID"`
  too). Full suite: 90/90 passing.
- Real, fresh-subprocess validation (RN-CUR-30) was run for all six
  surfaces: `cli check 007bbfb7`, `cli validate`, `search.diagnostics
  007bbfb7`, `cli probe`, `cli desk-check-persist 007bbfb7` - all
  produced short, well-formed summaries with correct `Full detail:`
  paths, and the persisted files were spot-checked (`validation-report.txt`)
  to confirm real content survived the change.
- Any future new CLI command or diagnostic script under
  `src/curriculum/` must follow this same pattern from the start
  (`write_detail` + `print_summary`), not reintroduce unbounded
  printing.

## Alternatives considered

- **A `--verbose` flag that prints full detail inline.** Rejected per
  the governing prompt's own explicit instruction: such a flag "may
  exist but must never be used in the normal flow," and since nothing
  in this session's own workflow would ever pass it, adding it now
  would only be a speculative, untested code path (against the
  project's own no-speculative-code convention).
- **Truncating in place at the print call site, no shared helper.**
  Rejected: six call sites each hand-rolling "write first N lines, then
  a path" is the kind of near-duplication CLAUDE.md's own file/function
  conventions ask to avoid, and a shared helper makes the 15-line cap a
  single, testable constant instead of six independently-drifting
  literals.
