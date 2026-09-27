"""CLI entry point: run before every `kaggle kernels push`.

Exits non-zero if the notebook uses a name that is never imported or
defined in any earlier cell, the drift class that made ADR 0032's fix
and, again, ADR 0049's per-task time-ceiling fix silently inactive on
real Kaggle hardware (`ast.parse` alone did not catch either).

Usage: python -m src.evaluation.run_notebook_name_check
"""
import sys
from pathlib import Path

from src.evaluation.notebook_name_check import check_notebook_undefined_names

DEFAULT_NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[2]
    / "notebooks"
    / "kaggle_submission_symbolic.ipynb"
)


def main(notebook_path: Path = DEFAULT_NOTEBOOK_PATH) -> int:
    issues = check_notebook_undefined_names(notebook_path)
    if not issues:
        print(f"OK: no undefined names found in {notebook_path.name}")
        return 0
    print(f"FOUND {len(issues)} undefined name issue(s) in {notebook_path.name}:")
    for issue in issues:
        print(f"  cell {issue.cell_index}, line {issue.line}: {issue.message}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
