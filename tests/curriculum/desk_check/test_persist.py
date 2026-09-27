"""Tests for Item 4's desk-check artifact persistence, on real 007bbfb7 data.

Uses monkeypatch to redirect persist.py's OUTPUTS_DIR/DOCS_DIR into tmp_path,
so this test never touches the real outputs/docs desk-check paths - those are
populated separately, for real, via `python -m src.curriculum.cli
desk-check-persist 007bbfb7` (RN-CUR-30).
"""
import json
from pathlib import Path

from src.curriculum.desk_check import persist
from src.curriculum.desk_check.run import run_desk_check
from src.curriculum.evaluator.solutions import load_task_solutions
from src.curriculum.loader import load_task
from src.curriculum.search.compose import Composition

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def test_hypothesis_id_is_deterministic_from_sorted_params():
    candidate = Composition(
        layout_name="block_grid",
        layout_params={"scale_cols": 3, "background": 0, "scale_rows": 3},
        selector_name="input_cell_not_background",
        selector_params={"background": 0},
        selected_content_name="copy",
        selected_content_params={},
        not_selected_content_name="fill",
        not_selected_content_params={"fill_color": 0},
    )

    assert persist.hypothesis_id(candidate) == (
        "block_grid-background=0_scale_cols=3_scale_rows=3"
        "__input_cell_not_background-background=0"
        "__copy"
        "__fill-fill_color=0"
    )


def test_build_hypothesis_record_007bbfb7_agrees_on_every_train_and_test_pair():
    task = load_task(TRAINING_DIR / "007bbfb7.json")
    gabarito = load_task_solutions(TRAINING_DIR / "007bbfb7.json")
    report = run_desk_check(task)
    candidate = report.verified[0]

    record = persist.build_hypothesis_record(task, candidate, gabarito)

    assert record["task_id"] == "007bbfb7"
    assert record["hypothesis_id"] == persist.hypothesis_id(candidate)
    assert len(record["train_pairs"]) == len(task.train)
    assert len(record["test_pairs"]) == len(task.test_inputs)
    assert all(p["matches_expected"] for p in record["train_pairs"])
    assert all(p["matches_expected"] for p in record["test_pairs"])
    assert record["all_pairs_agree"] is True


def test_write_desk_check_artifacts_writes_json_and_markdown(tmp_path, monkeypatch):
    monkeypatch.setattr(persist, "OUTPUTS_DIR", tmp_path / "outputs")
    monkeypatch.setattr(persist, "DOCS_DIR", tmp_path / "docs")

    task = load_task(TRAINING_DIR / "007bbfb7.json")
    report = run_desk_check(task)

    md_path = persist.write_desk_check_artifacts(task, report, solutions_dir=TRAINING_DIR)

    assert md_path == tmp_path / "docs" / "007bbfb7.md"
    assert md_path.exists()
    assert "007bbfb7" in md_path.read_text(encoding="utf-8")

    json_files = list((tmp_path / "outputs" / "007bbfb7").glob("*.json"))
    assert len(json_files) == len(report.verified)
    for path in json_files:
        record = json.loads(path.read_text(encoding="utf-8"))
        assert record["all_pairs_agree"] is True
