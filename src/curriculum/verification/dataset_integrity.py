"""Probe 1: local dataset presence and integrity, PRD Section 14 item 1.

Checks file counts (training=1000, evaluation=120), JSON validity, grid
rectangularity, and cell values in range 0-9, across every task file.
"""
import json
from pathlib import Path
from typing import List, Tuple

from src.curriculum.verification.types import (
    STATUS_ABSENT,
    STATUS_PRESENT,
    ProbeResult,
)

EXPECTED_TRAINING_COUNT = 1000
EXPECTED_EVALUATION_COUNT = 120


def _grid_is_valid(grid) -> bool:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return False
    width = len(grid[0])
    if width == 0:
        return False
    for row in grid:
        if len(row) != width:
            return False
        if not all(isinstance(cell, int) and 0 <= cell <= 9 for cell in row):
            return False
    return True


def _check_task_file(path: Path) -> Tuple[bool, str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"{path.name}: invalid JSON ({exc})"
    if not isinstance(raw, dict) or "train" not in raw or "test" not in raw:
        return False, f"{path.name}: missing 'train'/'test' keys"
    for split in ("train", "test"):
        for pair in raw[split]:
            for key in ("input", "output"):
                if key not in pair or not _grid_is_valid(pair[key]):
                    return False, f"{path.name}: malformed grid in {split}/{key}"
    return True, ""


def _scan_directory(directory: Path) -> Tuple[int, List[str]]:
    files = sorted(directory.glob("*.json"))
    errors = []
    for path in files:
        ok, message = _check_task_file(path)
        if not ok:
            errors.append(message)
    return len(files), errors


def check_dataset_integrity(data_root: Path) -> ProbeResult:
    training_dir = data_root / "training"
    evaluation_dir = data_root / "evaluation"
    raw_output = []

    if not training_dir.is_dir() or not evaluation_dir.is_dir():
        return ProbeResult(
            probe_id="probe1_dataset_integrity",
            title="Local dataset presence and integrity",
            status=STATUS_ABSENT,
            summary=f"training/evaluation directories not found under {data_root}",
            raw_output=[str(training_dir), str(evaluation_dir)],
        )

    training_count, training_errors = _scan_directory(training_dir)
    evaluation_count, evaluation_errors = _scan_directory(evaluation_dir)

    raw_output.append(f"training files: {training_count} (expected {EXPECTED_TRAINING_COUNT})")
    raw_output.append(f"evaluation files: {evaluation_count} (expected {EXPECTED_EVALUATION_COUNT})")
    raw_output.append(f"training malformed: {len(training_errors)}")
    raw_output.append(f"evaluation malformed: {len(evaluation_errors)}")
    raw_output += training_errors[:20]
    raw_output += evaluation_errors[:20]

    counts_ok = training_count == EXPECTED_TRAINING_COUNT and evaluation_count == EXPECTED_EVALUATION_COUNT
    no_malformed = not training_errors and not evaluation_errors

    if counts_ok and no_malformed:
        return ProbeResult(
            probe_id="probe1_dataset_integrity",
            title="Local dataset presence and integrity",
            status=STATUS_PRESENT,
            summary=(
                f"{training_count} training + {evaluation_count} evaluation files, "
                "all valid JSON, all grids rectangular with values 0-9."
            ),
            raw_output=raw_output,
        )
    return ProbeResult(
        probe_id="probe1_dataset_integrity",
        title="Local dataset presence and integrity",
        status=STATUS_ABSENT,
        summary=(
            f"counts_ok={counts_ok}, no_malformed={no_malformed}; "
            f"{len(training_errors)} training + {len(evaluation_errors)} evaluation malformed files."
        ),
        raw_output=raw_output,
    )
