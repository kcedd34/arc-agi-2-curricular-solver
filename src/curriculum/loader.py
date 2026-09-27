"""Solver-facing task loading, PRD Section 9.1.

RN-CUR-03 (gabarito inaccessible to solver) is enforced by construction
here, not by convention: `Task.test_inputs` holds only input grids for
the test pairs, never their outputs. There is structurally no field on
this type a solver could read to see a test answer. The only place test
outputs are ever loaded from disk is `src/curriculum/evaluator/solutions.py`,
which is not imported by anything under `src/curriculum/library/`,
`spec/`, or `search/` (the solver-facing code).

Per ADR 0061's reuse decision (RN-CUR-02), this reuses only the JSON-
reading mechanics of the prior line's `src/utils/task_loader.py`, not its
`Pair`/`Task` type shape (that module's `Pair` embeds `output` for every
pair, including test pairs, which would leak the gabarito here).
"""
import json
from pathlib import Path
from typing import Dict, List, NamedTuple

from src.curriculum.grid import Grid, is_valid_grid


class TrainPair(NamedTuple):
    input: Grid
    output: Grid


class Task(NamedTuple):
    task_id: str
    train: List[TrainPair]
    test_inputs: List[Grid]


def load_task(path: Path) -> Task:
    """Load one task file, keeping only test inputs, never test outputs."""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    train = [TrainPair(p["input"], p["output"]) for p in raw["train"]]
    for pair in train:
        if not is_valid_grid(pair.input) or not is_valid_grid(pair.output):
            raise ValueError(f"{path}: invalid grid in a train pair")
    test_inputs = [p["input"] for p in raw["test"]]
    for grid in test_inputs:
        if not is_valid_grid(grid):
            raise ValueError(f"{path}: invalid grid in a test input")
    return Task(task_id=path.stem, train=train, test_inputs=test_inputs)


def load_task_set(directory: Path) -> Dict[str, Task]:
    """Load every *.json task file in directory, keyed by task id."""
    tasks = {}
    for path in sorted(directory.glob("*.json")):
        task = load_task(path)
        tasks[task.task_id] = task
    return tasks
