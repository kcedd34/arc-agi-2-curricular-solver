"""Loading tasks from the public ARC-AGI-2 dataset."""
import json
from pathlib import Path
from typing import Dict, List, NamedTuple

from src.utils.grid_types import Grid


class Pair(NamedTuple):
    input: Grid
    output: Grid


class Task(NamedTuple):
    task_id: str
    train: List[Pair]
    test: List[Pair]


def load_task(path: Path) -> Task:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    train = [Pair(p["input"], p["output"]) for p in raw["train"]]
    test = [Pair(p["input"], p["output"]) for p in raw["test"]]
    return Task(task_id=path.stem, train=train, test=test)


def load_task_set(directory: Path) -> Dict[str, Task]:
    tasks = {}
    for path in sorted(directory.glob("*.json")):
        task = load_task(path)
        tasks[task.task_id] = task
    return tasks
