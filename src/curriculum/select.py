"""Pick the next curricular-pool task not yet solved, RN-CUR-05.

Selection never touches the probe pool: that partition exists purely
for contamination control (docs/curriculum/partition.json), never for
picking what to work on next.
"""
import json
from pathlib import Path
from typing import List, Optional

from src.curriculum.state import CurriculumState

DEFAULT_PARTITION_PATH = Path("docs/curriculum/partition.json")


def load_curricular_pool(path: Path = DEFAULT_PARTITION_PATH) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return raw["curricular_pool"]


def select_next_task(state: CurriculumState, curricular_pool: List[str]) -> Optional[str]:
    """First curricular-pool task, in pool order, not already in state.solved_tasks."""
    solved = set(state.solved_tasks)
    for task_id in curricular_pool:
        if task_id not in solved:
            return task_id
    return None
