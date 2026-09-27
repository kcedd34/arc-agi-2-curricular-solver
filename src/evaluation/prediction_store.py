"""Persists and loads raw solver predictions, one file per task.

Lets a later analysis (e.g. error diagnostics) reuse a completed
evaluation run's actual predicted grids without repeating expensive
inference. See docs/decisions/0007-raw-prediction-persistence.md.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

from src.utils.grid_types import Grid

PredictionsPerTask = List[List[Grid]]


def save_predictions(task_id: str, predictions_per_pair: PredictionsPerTask, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{task_id}.json"
    path.write_text(json.dumps(predictions_per_pair), encoding="utf-8")


def load_predictions(task_id: str, output_dir: Path) -> Optional[PredictionsPerTask]:
    path = output_dir / f"{task_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_all_predictions(output_dir: Path) -> Dict[str, PredictionsPerTask]:
    if not output_dir.exists():
        return {}
    return {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in output_dir.glob("*.json")}
