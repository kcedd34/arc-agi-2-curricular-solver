"""Gold test outputs and the oracle-augmented task (diagnostic only, ADR 0111)."""
from pathlib import Path
from typing import List

from src.curriculum.grid import Grid
from src.curriculum.loader import Task, TrainPair

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def load_gold(task_id: str, directory: Path = TRAINING_DIR) -> List[Grid]:
    import json

    raw = json.loads((directory / f"{task_id}.json").read_text(encoding="utf-8"))
    return [pair["output"] for pair in raw["test"]]


def oracle_task(task: Task, gold: List[Grid]) -> Task:
    """The train pairs plus every test pair, as if the gold were demonstrated."""
    extra = [TrainPair(grid, out) for grid, out in zip(task.test_inputs, gold)]
    return Task(task.task_id, list(task.train) + extra, task.test_inputs)
