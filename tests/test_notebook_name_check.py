import json
from pathlib import Path

from src.evaluation.notebook_name_check import (
    check_notebook_undefined_names,
    concatenate_cells,
    find_undefined_names,
)

REAL_NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[1]
    / "notebooks"
    / "kaggle_submission_symbolic.ipynb"
)


def _write_notebook(tmp_path, cells):
    notebook = {"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    path = tmp_path / "test.ipynb"
    path.write_text(json.dumps(notebook), encoding="utf-8")
    return path


def test_concatenate_cells_tracks_starting_line_per_cell():
    cells = ["a = 1\nb = 2", "c = 3"]

    source, cell_start_lines = concatenate_cells(cells)

    assert source == "a = 1\nb = 2\n\nc = 3\n"
    assert cell_start_lines == [1, 4]


def test_name_defined_in_earlier_cell_is_not_flagged():
    cells = [
        "from transformers import StoppingCriteria, StoppingCriteriaList",
        "StoppingCriteriaList([])",
    ]
    source, cell_start_lines = concatenate_cells(cells)

    issues = find_undefined_names(source, cell_start_lines)

    assert issues == []


def test_reproduces_the_real_stoppingcriterialist_regression():
    """Same shape as ADR 0049's fourth-round bug: StoppingCriteria is
    imported but StoppingCriteriaList, used two cells later, is not."""
    cells = [
        "from transformers import StoppingCriteria",
        "class DeadlineStoppingCriteria(StoppingCriteria):\n    pass",
        "stop = StoppingCriteriaList([DeadlineStoppingCriteria()])",
    ]
    source, cell_start_lines = concatenate_cells(cells)

    issues = find_undefined_names(source, cell_start_lines)

    assert len(issues) == 1
    assert issues[0].cell_index == 3
    assert "StoppingCriteriaList" in issues[0].message


def test_fixing_the_import_clears_the_regression():
    cells = [
        "from transformers import StoppingCriteria, StoppingCriteriaList",
        "class DeadlineStoppingCriteria(StoppingCriteria):\n    pass",
        "stop = StoppingCriteriaList([DeadlineStoppingCriteria()])",
    ]
    source, cell_start_lines = concatenate_cells(cells)

    issues = find_undefined_names(source, cell_start_lines)

    assert issues == []


def test_check_notebook_undefined_names_reads_a_real_file(tmp_path):
    cells = [
        {"cell_type": "code", "source": ["undefined_variable_xyz"]},
    ]
    path = _write_notebook(tmp_path, cells)

    issues = check_notebook_undefined_names(path)

    assert len(issues) == 1
    assert issues[0].cell_index == 1


def test_current_kaggle_submission_notebook_has_no_undefined_names():
    """Regression guard for the real notebook: fails again if the
    StoppingCriteriaList-style import gap ever reappears in Part C, or
    any other name is used without being imported/defined anywhere."""
    issues = check_notebook_undefined_names(REAL_NOTEBOOK_PATH)

    assert issues == [], issues
