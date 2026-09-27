from pathlib import Path

from src.curriculum.evaluator.solutions import load_task_solutions

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def test_load_task_solutions_007bbfb7():
    solutions = load_task_solutions(TRAINING_DIR / "007bbfb7.json")
    assert len(solutions) == 1
    assert len(solutions[0]) == 9
    assert len(solutions[0][0]) == 9
