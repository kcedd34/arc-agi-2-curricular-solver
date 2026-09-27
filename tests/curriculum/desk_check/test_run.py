"""Tests for desk_check/run.py on real 007bbfb7 data."""
from pathlib import Path

from src.curriculum.desk_check.run import run_desk_check
from src.curriculum.loader import load_task

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def test_run_desk_check_solved_007bbfb7():
    task = load_task(TRAINING_DIR / "007bbfb7.json")
    report = run_desk_check(task)

    assert report.task_id == "007bbfb7"
    assert report.status == "solved"
    assert len(report.verified) >= 1
    assert len(report.candidate_traces) == len(report.verified)
    for trace in report.candidate_traces:
        assert len(trace.steps_per_train_pair) == len(task.train)
        assert all(count > 0 for count in trace.steps_per_train_pair)
    assert report.prediction_shapes is not None
    assert len(report.prediction_shapes) == len(task.test_inputs)


def test_run_desk_check_no_candidate_when_layout_pieces_empty():
    import src.curriculum.search.compose as compose_mod

    task = load_task(TRAINING_DIR / "007bbfb7.json")
    original_layouts = compose_mod.LAYOUT_PIECES
    try:
        compose_mod.LAYOUT_PIECES = {}
        report = run_desk_check(task)
        assert report.status == "no_candidate"
        assert report.verified == []
        assert report.candidate_traces == []
        assert report.prediction_shapes is None
    finally:
        compose_mod.LAYOUT_PIECES = original_layouts
