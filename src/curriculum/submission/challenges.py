"""Loads the official combined challenges file (task_id -> {train, test}).

Test pairs carry no `output`; `Task.test_inputs` holds inputs only.
"""
import json
from pathlib import Path
from typing import Dict

from src.curriculum.loader import Task, TrainPair


def load_challenges(path: Path) -> Dict[str, Task]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {task_id: _build_task(task_id, entry) for task_id, entry in raw.items()}


def _build_task(task_id: str, entry: dict) -> Task:
    train = [TrainPair(p["input"], p["output"]) for p in entry["train"]]
    return Task(task_id=task_id, train=train, test_inputs=[p["input"] for p in entry["test"]])
