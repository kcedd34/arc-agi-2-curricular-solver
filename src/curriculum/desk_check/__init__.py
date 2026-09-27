"""Automated desk-check runner and report, PRD Section 9.1.

- run.py: `run_desk_check(task)` runs search/rank.py's `search_task`,
  then re-runs the interpreter on every verified candidate to collect a
  per-train-pair trace step count (RN-CUR-14: a human-auditable signal,
  never a raw grid dump).
- report.py: `format_report(report)` renders that result as plain text
  for a human reviewer - candidate names/params, trace step counts,
  predicted test output shapes (not content), and the ADR 0038
  ambiguity-bar message when `status == "ambiguous"`.
"""
