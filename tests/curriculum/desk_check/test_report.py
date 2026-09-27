"""Tests for desk_check/report.py on synthetic DeskCheckReport values (no GPU/disk needed)."""
from src.curriculum.desk_check.report import format_report
from src.curriculum.desk_check.run import CandidateTrace, DeskCheckReport
from src.curriculum.search.compose import Composition


def test_format_report_solved():
    candidate = Composition(
        layout_name="block_grid",
        layout_params={"scale_rows": 3, "scale_cols": 3},
        selector_name="input_cell_not_background",
        selector_params={"background": 0},
        selected_content_name="copy",
        selected_content_params={},
        not_selected_content_name="fill",
        not_selected_content_params={"fill_color": 0},
    )
    report = DeskCheckReport(
        task_id="007bbfb7",
        status="solved",
        unanimous=True,
        verified=[candidate],
        candidate_traces=[CandidateTrace(candidate=candidate, steps_per_train_pair=[6, 6, 6, 6, 6])],
        prediction_shapes=[(9, 9)],
    )
    text = format_report(report)
    assert "Task: 007bbfb7" in text
    assert "Unanimous" in text and "True" in text
    assert "block_grid" in text
    assert "9x9" in text


def test_format_report_no_candidate():
    report = DeskCheckReport(
        task_id="x", status="no_candidate", unanimous=False, verified=[], candidate_traces=[], prediction_shapes=None
    )
    text = format_report(report)
    assert "No verified candidate found." in text


def test_format_report_ambiguous():
    c1 = Composition(
        layout_name="block_grid",
        layout_params={"scale_rows": 1, "scale_cols": 1},
        selector_name="row_parity",
        selector_params={},
        selected_content_name="copy",
        selected_content_params={},
        not_selected_content_name="copy",
        not_selected_content_params={},
    )
    c2 = Composition(
        layout_name="block_grid",
        layout_params={"scale_rows": 2, "scale_cols": 2},
        selector_name="row_parity",
        selector_params={},
        selected_content_name="copy",
        selected_content_params={},
        not_selected_content_name="copy",
        not_selected_content_params={},
    )
    report = DeskCheckReport(
        task_id="x",
        status="ambiguous",
        unanimous=False,
        verified=[c1, c2],
        candidate_traces=[
            CandidateTrace(candidate=c1, steps_per_train_pair=[2]),
            CandidateTrace(candidate=c2, steps_per_train_pair=[3]),
        ],
        prediction_shapes=None,
    )
    text = format_report(report)
    assert "AMBIGUOUS" in text
    assert "ADR 0038" in text
