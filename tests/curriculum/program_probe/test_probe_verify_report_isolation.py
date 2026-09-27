import json
from pathlib import Path

from src.curriculum.program_probe.report import build_report, counted, projection
from src.curriculum.program_probe.verify import verify_program

SRC = Path("src")
PROBE = Path("src/curriculum/program_probe")


def _write_task(directory: Path):
    task = {
        "train": [{"input": [[1, 0]], "output": [[2, 0]]}, {"input": [[0, 1]], "output": [[0, 2]]}],
        "test": [{"input": [[1, 1]], "output": [[2, 2]]}],
    }
    (directory / "t0000001.json").write_text(json.dumps(task), encoding="utf-8")


RECOLOR = "def solve(grid):\n    return [[2 if v else 0 for v in row] for row in grid]\n"
CONSTANT = "def solve(grid):\n    return [[2, 0]]\n"
TRAIN_ONLY = "def solve(grid):\n    return [[2 if v else 0 for v in row] for row in grid][:1] if len(grid[0]) == 2 and grid != [[1, 1]] else [[9]]\n"


def test_correct_program_passes_train_and_test(tmp_path):
    _write_task(tmp_path)
    verdict = verify_program(RECOLOR, "t0000001", tmp_path)
    assert (verdict.executes, verdict.train_ok, verdict.test_ok) == (True, True, True)
    assert not verdict.flags["suspicious"]


def test_wrong_program_never_reaches_the_test_gold(tmp_path):
    _write_task(tmp_path)
    verdict = verify_program(CONSTANT, "t0000001", tmp_path)
    assert verdict.train_ok is False and verdict.test_ok is None and verdict.flags is None


def test_train_only_program_is_partial_signal(tmp_path):
    _write_task(tmp_path)
    verdict = verify_program(TRAIN_ONLY, "t0000001", tmp_path)
    assert verdict.train_ok and verdict.test_ok is False


def test_flagged_program_does_not_count():
    row = {"train_ok": True, "flags": {"suspicious": True}, "test_ok": True}
    assert not counted(row)


def test_report_counts_tasks_and_projects_cost():
    good = {"model": "base", "variant": "plain", "task_id": "a", "temperature": 0.7, "seconds": 7.0,
            "executes": True, "train_ok": True, "test_ok": True, "flags": {"suspicious": False}}
    bad = {**good, "task_id": "b", "train_ok": False, "test_ok": None, "flags": None}
    report = build_report([good, bad])
    assert report["overall"]["train_ok_tasks"] == ["a"] and report["overall"]["test_ok_tasks"] == ["a"]
    assert projection(7.0)["hours"] == 7.0 * 2400 / 3600


def test_no_production_module_imports_the_probe():
    needles = ("curriculum.program_probe", "curriculum import program_probe")
    offenders = [
        str(p) for p in SRC.rglob("*.py") if PROBE not in p.parents and any(
            n in line for line in p.read_text(encoding="utf-8").splitlines() if line.lstrip().startswith(("import ", "from ")) for n in needles
        )
    ]
    assert offenders == []


def test_probe_docstring_states_it_is_diagnostic_only():
    assert "DIAGNOSTIC ONLY" in (PROBE / "__init__.py").read_text(encoding="utf-8")
