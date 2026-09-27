# 0065 - CLAUDE.md stays lean and stable (RN-CUR-34)

Status: Accepted (2026-09-21)

## Context

`CLAUDE.md` had grown to 169,852 bytes (~66.4k tokens), loaded in full
at the start of every session. The root cause was procedural: every ADR
accepted since the project started was also propagated into this file's
old Sections 5 ("How this project makes decisions", a narrative list of
every ADR) and 6 ("Current project state", an ever-growing prose log),
with no upper bound. This caused repeated autocompact thrashing, since
a large fraction of the context window was consumed by this one file
before any real work began.

## Decision

- `CLAUDE.md` is rewritten to contain only: active mode (curricular
  restart + BOOTSTRAP.md precedence), short code conventions, context
  hygiene rules, and pointers to where history/indices live in `docs/`.
- The full pre-rewrite `CLAUDE.md` is archived verbatim, nothing
  deleted, at `docs/history/claude-md-archive.md`.
- `docs/decisions/README.md` is the new canonical ADR index: one line
  per ADR (number, title, status), built via grep against each ADR's
  own title/status lines, never by opening or summarizing full ADR
  bodies.
- **Propagation rule change:** from now on, ADRs are never summarized
  into `CLAUDE.md`. A new ADR gets exactly one line in
  `docs/decisions/README.md`. This is the rule that failed before; this
  ADR changes it going forward, it does not just treat one symptom.
- A test, `tests/test_claude_md_size.py`, fails if `CLAUDE.md` exceeds
  12 KB, so the failure mode has an automated guard instead of relying
  on discipline alone.
- This decision is also recorded as RN-CUR-34 in
  `docs/curriculum/BOOTSTRAP.md`'s amendments section, since it governs
  curricular-mode session hygiene going forward, not just this one
  file.

## Consequences

- `CLAUDE.md` dropped from 169,852 bytes to 4,281 bytes.
- Every future ADR must remember to add its own one-line entry to
  `docs/decisions/README.md` (not automated by this ADR; a manual step
  per new ADR, same discipline as updating `CLAUDE.md` used to be).
- Anyone wanting the old, fully-narrated project history reads
  `docs/history/claude-md-archive.md` or the ADRs directly; that detail
  is no longer available by reading `CLAUDE.md` alone.

## Alternatives considered

- **Keep summarizing ADRs into `CLAUDE.md` but prune old entries
  periodically.** Rejected: requires an ongoing manual judgment call
  about what is safe to cut, which is exactly the discipline that
  already failed once; a hard size limit plus an index file needs no
  judgment call.
- **Split `CLAUDE.md` into multiple always-loaded files instead of one
  short file plus pointers.** Rejected: multiple always-loaded files
  have the same unbounded-growth failure mode as one file, just spread
  across more places.
