"""Runs the trivial baseline against the public dataset and prints the score.

Usage: python -m src.evaluation.run_baseline [training|evaluation]
"""
import sys
from pathlib import Path

from src.evaluation.harness import evaluate_solver_on_directory
from src.solvers.baseline_solver import solve_task

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    data_dir = DATA_ROOT / split
    predictions_dir = PROJECT_ROOT / "outputs" / "predictions" / "baseline" / split
    result = evaluate_solver_on_directory(solve_task, data_dir, predictions_dir=predictions_dir)
    print(f"split={split}")
    print(f"test_pairs_total={result.total_test_pairs}")
    print(f"test_pairs_correct={result.correct_test_pairs}")
    print(f"accuracy={result.accuracy:.4f}")


if __name__ == "__main__":
    main()
