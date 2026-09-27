"""Loads gabaritos (test-pair outputs), PRD Section 9.1.

RN-CUR-03: this is the only module in src/curriculum/ that reads test
outputs from a task's JSON file. It is imported only by evaluator code
(exact_match.py and, later, curriculum-state validation/probe modules
that measure accuracy) - never by src/curriculum/library/, spec/, or
search/, which is what makes RN-CUR-03 a structural guarantee rather
than a convention. See tests/curriculum/evaluator/ for the automated
check that solver-facing modules do not import this one.
"""
import json
from pathlib import Path
from typing import Dict, List

from src.curriculum.grid import Grid, is_valid_grid


def load_task_solutions(path: Path) -> List[Grid]:
    """Return the list of gabarito grids, one per test pair, for one task."""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    solutions = [p["output"] for p in raw["test"]]
    for grid in solutions:
        if not is_valid_grid(grid):
            raise ValueError(f"{path}: invalid grid in a test solution")
    return solutions


def load_solution_set(directory: Path) -> Dict[str, List[Grid]]:
    """Return {task_id: [gabarito grids]} for every *.json file in directory."""
    solutions = {}
    for path in sorted(directory.glob("*.json")):
        solutions[path.stem] = load_task_solutions(path)
    return solutions
