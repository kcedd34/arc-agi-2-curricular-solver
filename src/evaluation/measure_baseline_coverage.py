"""Measures the existing symbolic baseline's (`src/solvers/baseline_solver.py`,
geometry/color only, ADR 0001) real exact-match coverage against the same
40-task validation-tier sample ADR 0034 used for the neural solver, so the
two numbers are directly comparable. See ADR 0040/0041.

Usage: python -m src.evaluation.measure_baseline_coverage
"""
import json
from pathlib import Path

from src.evaluation.harness import evaluate_solver_on_directory
from src.solvers.baseline_solver import solve_task

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data" / "evaluation"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "diagnostics" / "baseline_coverage_validation_tier.json"


def main() -> None:
    result = evaluate_solver_on_directory(solve_task, DATA_ROOT, tier="validation")
    solved_task_ids = sorted(
        task_id for task_id, correct in result.per_task_correct.items() if correct > 0
    )
    print(f"tasks_total={len(result.per_task_total)}")
    print(f"test_pairs_total={result.total_test_pairs}")
    print(f"test_pairs_correct={result.correct_test_pairs}")
    print(f"exact_match_rate={result.accuracy:.4f}")
    print(f"tasks_with_at_least_one_correct_pair={len(solved_task_ids)}")
    print(f"solved_task_ids={solved_task_ids}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "tasks_total": len(result.per_task_total),
                "test_pairs_total": result.total_test_pairs,
                "test_pairs_correct": result.correct_test_pairs,
                "exact_match_rate": result.accuracy,
                "solved_task_ids": solved_task_ids,
                "per_task_correct": result.per_task_correct,
                "per_task_total": result.per_task_total,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
