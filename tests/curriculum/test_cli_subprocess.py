"""Real-subprocess guard for RN-CUR-30 (docs/curriculum/BOOTSTRAP.md amendments).

Deliberately does NOT import src.curriculum.library.primitives anywhere in
this file. Every other cli test file does import it (directly or via a
fixture module), which is exactly what let the empty-REGISTRY bug (fixed in
src/curriculum/search/enumerate.py) hide behind 75 passing tests while a
real `python -m src.curriculum.cli solve 007bbfb7` failed with
`Status: no_candidate`. Running the CLI as a real subprocess reproduces the
same fresh-import-graph conditions as a real invocation; an in-process call
would not, since pytest's own import graph (via other already-imported test
modules) can mask the same gap this test exists to catch.
"""
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "src.curriculum.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_solve_007bbfb7_finds_a_candidate_in_a_fresh_process(tmp_path):
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "updated_at": "2026-09-21",
                "current_stage": "stage_1",
                "stage_status": "in_progress",
                "partition_ref": {
                    "path": "docs/curriculum/partition.json",
                    "seed": 20260921,
                    "total_training_tasks": 1000,
                    "curricular_pool_size": 800,
                    "probe_pool_size": 200,
                    "pinned_curricular_task_ids": ["007bbfb7"],
                },
                "remaining_stage_0_items": [],
                "blocked_on": [],
                "solved_tasks": [],
                "next_task": "007bbfb7",
                "probe_pool_checkpoints": [],
            }
        )
    )

    result = _run_cli("solve", "007bbfb7", cwd=PROJECT_ROOT)

    assert result.returncode == 0, result.stderr
    assert "no_candidate" not in result.stdout
    assert "Solved (gabarito-verified): True" in result.stdout


def test_check_007bbfb7_is_solved_in_a_fresh_process():
    result = _run_cli("check", "007bbfb7", cwd=PROJECT_ROOT)

    assert result.returncode == 0, result.stderr
    assert "no_candidate" not in result.stdout
    assert "Unanimous (not gabarito-verified): True" in result.stdout
