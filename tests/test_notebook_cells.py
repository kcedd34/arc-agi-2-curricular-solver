import json

from src.evaluation.notebook_cells import extract_code_cells


def _write_notebook(tmp_path, cells):
    notebook = {
        "cells": cells,
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path = tmp_path / "test.ipynb"
    path.write_text(json.dumps(notebook), encoding="utf-8")
    return path


def test_extracts_only_code_cells_in_order(tmp_path):
    cells = [
        {"cell_type": "markdown", "source": ["# Title\n"]},
        {"cell_type": "code", "source": ["import os\n", "x = 1\n"]},
        {"cell_type": "markdown", "source": ["Some notes"]},
        {"cell_type": "code", "source": ["y = 2\n"]},
    ]
    path = _write_notebook(tmp_path, cells)

    result = extract_code_cells(path)

    assert result == ["import os\nx = 1\n", "y = 2\n"]


def test_empty_notebook_returns_empty_list(tmp_path):
    path = _write_notebook(tmp_path, [])

    assert extract_code_cells(path) == []
