from src.evaluation.pair_diagnostics import best_pair_diagnostic, dimension_match, per_cell_accuracy


def test_dimension_match_true_for_equal_shapes():
    assert dimension_match([[1, 2], [3, 4]], [[5, 6], [7, 8]]) is True


def test_dimension_match_false_for_different_shapes():
    assert dimension_match([[1, 2]], [[1, 2], [3, 4]]) is False


def test_per_cell_accuracy_partial_match():
    assert per_cell_accuracy([[1, 2], [3, 0]], [[1, 2], [3, 4]]) == 0.75


def test_per_cell_accuracy_none_on_dimension_mismatch():
    assert per_cell_accuracy([[1, 2]], [[1, 2], [3, 4]]) is None


def test_best_pair_diagnostic_picks_best_attempt():
    predictions = [[[9, 9], [9, 9]], [[1, 2], [3, 0]]]
    expected = [[1, 2], [3, 4]]
    dim_match, accuracy = best_pair_diagnostic(predictions, expected)
    assert dim_match is True
    assert accuracy == 0.75


def test_best_pair_diagnostic_no_predictions():
    assert best_pair_diagnostic([], [[1, 2]]) == (False, None)
