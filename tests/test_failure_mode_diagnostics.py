from src.evaluation.failure_mode_diagnostics import (
    has_degenerate_repetition,
    has_hallucinated_second_example,
    has_topic_drift,
)


def test_no_hallucination_on_a_clean_single_grid():
    completion = "123\n456\n789"
    assert has_hallucinated_second_example(completion) is False


def test_detects_second_input_marker_after_a_closed_grid():
    completion = "123\n456\n789\n\nOutput:\n123\n\nInput:\n999\n888\n\nOutput:\n111"
    assert has_hallucinated_second_example(completion) is True


def test_no_repetition_on_a_short_valid_grid():
    completion = "123\n456\n789"
    assert has_degenerate_repetition(completion) is False


def test_detects_long_run_of_identical_repeated_rows():
    completion = "123\n" + "\n".join(["6666666666666"] * 12)
    assert has_degenerate_repetition(completion) is True


def test_short_run_below_threshold_is_not_flagged():
    completion = "123\n" + "\n".join(["6666666666666"] * 5)
    assert has_degenerate_repetition(completion) is False


def test_blank_lines_do_not_count_as_a_repeated_run():
    completion = "\n".join([""] * 15)
    assert has_degenerate_repetition(completion) is False


def test_no_topic_drift_on_a_clean_grid():
    completion = "123\n456\n789"
    assert has_topic_drift(completion) is False


def test_detects_topic_drift_via_code_marker():
    completion = "123\n456\n789\n\n```python\nx = 1\n```"
    assert has_topic_drift(completion) is True


def test_detects_topic_drift_via_def_marker_without_fence():
    completion = "123\n456\n789\n\ndef invert_matrix(matrix):\n    pass"
    assert has_topic_drift(completion) is True


def test_detects_topic_drift_via_natural_language_line():
    completion = "123\n456\n789\n\nSure! Here is the Python code that inverts an 8 x 8 matrix:"
    assert has_topic_drift(completion) is True


def test_short_natural_language_line_below_word_threshold_is_not_flagged():
    completion = "123\n456\n789\n\nRow A B"
    assert has_topic_drift(completion) is False
