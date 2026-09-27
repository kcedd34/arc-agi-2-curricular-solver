from src.evaluation.diagnostic_runner import (
    DiagnosticPairRow,
    _any_shape_match,
    _count_copies_of_input,
    render_markdown,
)


def test_count_copies_of_input_counts_exact_matches_to_input():
    grid_input = [[1, 2], [3, 4]]
    predictions = [[[1, 2], [3, 4]], [[9, 9], [9, 9]], [[1, 2], [3, 4]]]
    assert _count_copies_of_input(predictions, grid_input) == 2


def test_count_copies_of_input_zero_when_no_predictions():
    assert _count_copies_of_input([], [[1, 2], [3, 4]]) == 0


def test_any_shape_match_none_when_nothing_kept():
    assert _any_shape_match([], [[1, 2], [3, 4]]) is None


def test_any_shape_match_true_when_one_prediction_matches_shape():
    expected = [[1, 2], [3, 4]]
    predictions = [[[9, 9, 9]], [[5, 6], [7, 8]]]
    assert _any_shape_match(predictions, expected) is True


def test_any_shape_match_false_when_no_prediction_matches_shape():
    expected = [[1, 2], [3, 4]]
    predictions = [[[9, 9, 9]]]
    assert _any_shape_match(predictions, expected) is False


def test_render_markdown_includes_shape_match_column():
    rows = [
        DiagnosticPairRow(
            "current_config", "task1", "test", 0,
            attempts_tried=2, num_parsed=2, num_kept=1,
            num_copies_of_input=0, exact_match=False, shape_matches_expected=True,
        ),
        DiagnosticPairRow(
            "current_config", "task2", "test", 0,
            attempts_tried=2, num_parsed=0, num_kept=0,
            num_copies_of_input=0, exact_match=False, shape_matches_expected=None,
        ),
    ]
    markdown = render_markdown(rows)
    assert "Shape match" in markdown
    assert "| task1 | test | 0 | 2 | 2 | 1 | 0 | no | yes |" in markdown
    assert "| task2 | test | 0 | 2 | 0 | 0 | 0 | no | n/a |" in markdown
