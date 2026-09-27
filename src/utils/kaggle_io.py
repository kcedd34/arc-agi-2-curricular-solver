"""Loading/writing the official Kaggle competition file formats.

Differs from `src.utils.task_loader` in two ways the local dataset never
exercises: all tasks live in one combined JSON object (task_id -> task),
not one file per task, and test pairs carry no `output` (that is exactly
what a real submission must predict). The placeholder used for that
missing field is never read on the solve/submission-build path (only
`src.evaluation.harness.evaluate_solver` reads `Pair.output`, and that
path is for local scoring against known answers, never for building a
submission), so an empty grid is enough to keep `Task`/`Pair` reusable
without changing solver or submission code.
"""
import json
from pathlib import Path
from typing import Dict

from src.utils.grid_types import Grid
from src.utils.task_loader import Pair, Task

NO_OUTPUT_PLACEHOLDER: Grid = [[0]]


def load_challenges(path: Path) -> Dict[str, Task]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {task_id: _build_task(task_id, entry) for task_id, entry in raw.items()}


def _build_task(task_id: str, entry: dict) -> Task:
    train = [Pair(p["input"], p["output"]) for p in entry["train"]]
    test = [Pair(p["input"], NO_OUTPUT_PLACEHOLDER) for p in entry["test"]]
    return Task(task_id=task_id, train=train, test=test)
