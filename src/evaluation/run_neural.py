"""Runs the neural solver against the public dataset and prints the score.

Usage: python -m src.evaluation.run_neural [training|evaluation] [limit|tier]

Second argument is either a raw integer `limit` (first N tasks, sorted by
task id) or a sampling tier name (`smoke`, `sanity`, `validation`, see ADR
0015). Omit it to run the full split.

Requires a CUDA GPU and downloads Qwen3-4B-Instruct-2507 (ADR 0051) from
Hugging Face on first run. Meant to run inside the project's WSL2 virtual
environment, see docs/neural-line.md, section "Running the neural solver".
"""
import sys
from pathlib import Path

from src.evaluation.harness import evaluate_solver_on_directory
from src.evaluation.sample_tiers import TIER_NAMES
from src.solvers.neural_solver import solve_task

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"


def _parse_sample_selector(raw: str):
    if raw in TIER_NAMES:
        return None, raw
    return int(raw), None


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    limit, tier = _parse_sample_selector(sys.argv[2]) if len(sys.argv) > 2 else (None, None)
    data_dir = DATA_ROOT / split
    predictions_dir = PROJECT_ROOT / "outputs" / "predictions" / "neural" / split
    result = evaluate_solver_on_directory(
        solve_task, data_dir, limit=limit, predictions_dir=predictions_dir, tier=tier
    )
    print(f"split={split}")
    print(f"limit={limit}")
    print(f"tier={tier}")
    print(f"test_pairs_total={result.total_test_pairs}")
    print(f"test_pairs_correct={result.correct_test_pairs}")
    print(f"accuracy={result.accuracy:.4f}")


if __name__ == "__main__":
    main()
