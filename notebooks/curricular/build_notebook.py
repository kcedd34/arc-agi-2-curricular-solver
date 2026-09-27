"""Generates the curricular Kaggle notebook with the solver source embedded (ADR 0104).

The notebook ships the exact `src/curriculum` tree as a base64 zip, so
Kaggle runs the code that the local test suite covers (no inlined copy
to drift). Usage: python notebooks/curricular/build_notebook.py
"""
import base64
import hashlib
import io
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "kaggle_submission_curricular.ipynb"

INTRO = """# ARC-AGI-2 - curricular symbolic solver submission (ADR 0104)

CPU only, no internet, no model. The solver source (`src/curriculum`) is embedded below as a
base64 zip and extracted at run time, so the notebook runs exactly the tested code. Solver:
verified candidates from the curricular library (main, objects, sequences), simplicity ranking,
up to two distinct attempts, ADR 0011 fallback when no candidate verifies. Each task runs in its
own process with a hard timeout; a global wall budget guards the total run time.

Output: `/kaggle/working/submission.json` (the only filename Kaggle accepts, ADR 0049)."""

EXTRACT = '''import base64, hashlib, io, os, sys, zipfile

CODE_SHA256 = "{sha}"
CODE_B64 = "{b64}"

_raw = base64.b64decode(CODE_B64)
assert hashlib.sha256(_raw).hexdigest() == CODE_SHA256, "embedded solver zip is corrupted"
WORK_DIR = "/kaggle/working" if os.path.isdir("/kaggle/working") else "."
SRC_ROOT = os.path.join(WORK_DIR, "curricular_src")
zipfile.ZipFile(io.BytesIO(_raw)).extractall(SRC_ROOT)
sys.path.insert(0, SRC_ROOT)
print("solver extracted to", SRC_ROOT, "sha256", CODE_SHA256[:12])
'''

RUN = '''import os
from pathlib import Path

from src.curriculum.parallel_batch import default_worker_count
from src.curriculum.submission.build import build_submission_file


def find_challenges_path():
    for root, _, files in os.walk("/kaggle/input"):
        for name in files:
            if name.endswith("test_challenges.json"):
                return Path(root) / name
    raise FileNotFoundError("no *test_challenges.json under /kaggle/input")


CHALLENGES = find_challenges_path()
OUTPUT = Path(WORK_DIR) / "submission.json"
REPORT = Path(WORK_DIR) / "submission_report.json"
WORKERS = default_worker_count()
print("challenges:", CHALLENGES, "| cpus:", os.cpu_count(), "| workers:", WORKERS)
SUMMARY = build_submission_file(CHALLENGES, OUTPUT, REPORT, WORKERS)
print("wall seconds:", SUMMARY["wall_seconds"], "| statuses:", SUMMARY["status_counts"])
print("tasks with a verified candidate:", SUMMARY["tasks_with_candidate"])
'''

CHECK = '''import json

from src.curriculum.submission.challenges import load_challenges
from src.curriculum.submission.format import validate_submission

_submission = json.loads(OUTPUT.read_text(encoding="utf-8"))
validate_submission(_submission, load_challenges(CHALLENGES))
print("submission.json re-read and validated:", len(_submission), "tasks,", OUTPUT.stat().st_size, "bytes")
'''


def _zip_source() -> bytes:
    buffer = io.BytesIO()
    files = [ROOT / "src" / "__init__.py"] + sorted((ROOT / "src" / "curriculum").rglob("*.py"))
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(ROOT).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            zf.writestr(info, path.read_bytes(), zipfile.ZIP_DEFLATED)
    return buffer.getvalue()


def _cell(kind: str, source: str) -> dict:
    cell = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        cell.update(execution_count=None, outputs=[])
    return cell


def build() -> Path:
    raw = _zip_source()
    extract = EXTRACT.format(sha=hashlib.sha256(raw).hexdigest(), b64=base64.b64encode(raw).decode("ascii"))
    cells = [_cell("markdown", INTRO), _cell("code", extract), _cell("code", RUN), _cell("code", CHECK)]
    notebook = {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
                "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                             "language_info": {"name": "python", "version": "3.12"}}}
    OUT.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
    return OUT


if __name__ == "__main__":
    print(build(), OUT.stat().st_size, "bytes")
