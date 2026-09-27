"""Tests for regression.py against real 007bbfb7 data."""
from pathlib import Path

from src.curriculum.regression import run_regression
import src.curriculum.search.compose as compose_mod

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def test_run_regression_no_regression_for_still_solved_task():
    result = run_regression(["007bbfb7"], TRAINING_DIR)

    assert result.checked == ["007bbfb7"]
    assert result.regressed == []


def test_run_regression_flags_task_that_no_longer_solves():
    original_layouts = compose_mod.LAYOUT_PIECES
    try:
        compose_mod.LAYOUT_PIECES = {}  # empty: nothing solves anymore
        result = run_regression(["007bbfb7"], TRAINING_DIR)
        assert result.checked == ["007bbfb7"]
        assert result.regressed == ["007bbfb7"]
    finally:
        compose_mod.LAYOUT_PIECES = original_layouts
