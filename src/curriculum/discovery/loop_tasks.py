"""Task lists of the closed loop (ADR 0110): the arc2_only training tasks, and
the subset somebody already read or taught (accepted solutions and the
hand-solved rounds), which never counts as "without teaching"."""
import json
from pathlib import Path
from typing import List, Set

from src.curriculum.diagnostics.origin import EXCLUSIVE, load_arc1_ids, origin_of
from src.curriculum.diagnostics.probe_by_origin import SEEN_ANY
from src.curriculum.state import DEFAULT_STATE_PATH

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")
HANDSOLVED_DIR = Path("docs/curriculum/handsolved")


def arc2_only_task_ids(training_dir: Path = TRAINING_DIR) -> List[str]:
    arc1 = load_arc1_ids()
    ids = sorted(path.stem for path in training_dir.glob("*.json"))
    return [task_id for task_id in ids if origin_of(task_id, arc1) == EXCLUSIVE]


def taught_task_ids() -> Set[str]:
    state = json.loads(Path(DEFAULT_STATE_PATH).read_text(encoding="utf-8"))
    hand = {path.stem for path in HANDSOLVED_DIR.glob("*.md")}
    return set(state["solved_tasks"]) | hand | set(SEEN_ANY)
