"""Probe 2: confirm task 007bbfb7 is present in the local training set.

PRD Section 14 item 2, the curricular restart's Stage 1 target task.
"""
import json
from pathlib import Path

from src.curriculum.verification.types import (
    STATUS_ABSENT,
    STATUS_PRESENT,
    ProbeResult,
)

STAGE1_TASK_ID = "007bbfb7"


def check_task_presence(data_root: Path, task_id: str = STAGE1_TASK_ID) -> ProbeResult:
    training_dir = data_root / "training"
    task_path = training_dir / f"{task_id}.json"

    if not task_path.is_file():
        return ProbeResult(
            probe_id="probe2_task_presence",
            title=f"Task {task_id} present in local training set",
            status=STATUS_ABSENT,
            summary=f"{task_path} does not exist.",
            raw_output=[str(task_path)],
        )

    try:
        with open(task_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return ProbeResult(
            probe_id="probe2_task_presence",
            title=f"Task {task_id} present in local training set",
            status=STATUS_ABSENT,
            summary=f"{task_path} exists but is not valid JSON ({exc}).",
            raw_output=[str(task_path), str(exc)],
        )

    train_count = len(raw.get("train", []))
    test_count = len(raw.get("test", []))
    raw_output = [
        str(task_path),
        f"train pairs: {train_count}",
        f"test pairs: {test_count}",
    ]

    return ProbeResult(
        probe_id="probe2_task_presence",
        title=f"Task {task_id} present in local training set",
        status=STATUS_PRESENT,
        summary=f"{task_id}.json found under training/, {train_count} train pairs, {test_count} test pairs.",
        raw_output=raw_output,
    )
