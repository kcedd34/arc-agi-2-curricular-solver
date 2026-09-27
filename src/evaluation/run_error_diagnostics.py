"""Runs the per-pair error diagnostic report against the public dataset.

Usage: python -m src.evaluation.run_error_diagnostics [training|evaluation] [limit]

Same split/limit semantics as run_neural.py. Prints the report as a
markdown table; does not decide or apply any improvement lever, this is
diagnosis only (see docs/decisions/0008-error-diagnosis-first-round.md).
"""
import sys
from pathlib import Path

from src.evaluation.error_report import build_error_report
from src.evaluation.error_report_markdown import render_error_report_markdown
from src.solvers.neural_solver import solve_task
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    data_dir = DATA_ROOT / split
    predictions_dir = PROJECT_ROOT / "outputs" / "predictions" / "neural" / split
    tasks = load_task_set(data_dir)
    if limit is not None:
        tasks = dict(list(tasks.items())[:limit])
    reports = build_error_report(solve_task, tasks, predictions_dir=predictions_dir)
    print(render_error_report_markdown(reports))


if __name__ == "__main__":
    main()
