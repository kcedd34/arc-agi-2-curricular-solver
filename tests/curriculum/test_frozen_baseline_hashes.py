import hashlib
import json
from pathlib import Path

FROZEN = Path("docs/curriculum/frozen-baseline.json")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_frozen_baseline_files_are_unchanged():
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))["sha256"]
    for name, expected in frozen.items():
        path = Path(name)
        if path.exists():
            assert _digest(path) == expected, f"{name} changed; the 0.83 baseline is frozen (ADR 0112)"


def test_frozen_manifest_lists_the_submitted_notebook_and_predictions():
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))["sha256"]
    assert "notebooks/curricular/kaggle_submission_curricular.ipynb" in frozen
    assert "outputs/curriculum/kaggle_run_v1/submission.json" in frozen
