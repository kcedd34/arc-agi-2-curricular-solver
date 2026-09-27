"""Builds submission.json from an official Kaggle challenges file, per ADR 0006/0047.

Runs the symbolic solver only (`src.solvers.baseline_solver`), no GPU/neural
dependency, so it can run inside the Kaggle scoring container with no
internet access. Usable both as a local dry run (pass a local path) and
inside the actual submission notebook (pass the competition's input path).
"""
import argparse
import time
from pathlib import Path

from src.solvers.baseline_solver import solve_task
from src.evaluation.submission_format import build_submission, validate_submission, write_submission
from src.utils.kaggle_io import load_challenges


def build_and_write(challenges_path: Path, output_path: Path) -> dict:
    tasks = load_challenges(challenges_path)
    start = time.monotonic()
    submission = build_submission(solve_task, tasks)
    elapsed = time.monotonic() - start

    validate_submission(submission, tasks)
    write_submission(submission, output_path)

    return {
        "task_count": len(tasks),
        "elapsed_seconds": elapsed,
        "output_path": str(output_path),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("challenges_path", type=Path, help="path to the official *_challenges.json file")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("submission.json"),
        help="where to write submission.json (default: ./submission.json)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = build_and_write(args.challenges_path, args.output)
    print(
        f"OK: {summary['task_count']} tasks solved and validated in "
        f"{summary['elapsed_seconds']:.2f}s -> {summary['output_path']}"
    )


if __name__ == "__main__":
    main()
