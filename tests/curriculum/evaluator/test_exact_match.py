from src.curriculum.evaluator.exact_match import is_exact_match, score_task


def test_is_exact_match_true():
    assert is_exact_match([[1, 2]], [[1, 2]])


def test_is_exact_match_false_content():
    assert not is_exact_match([[1, 2]], [[1, 3]])


def test_is_exact_match_false_shape():
    assert not is_exact_match([[1, 2]], [[1, 2], [3, 4]])


def test_score_task_all_correct():
    result = score_task([[[1]], [[2]]], [[[1]], [[2]]])
    assert result["num_exact_matches"] == 2
    assert result["all_exact_match"] is True


def test_score_task_partial():
    result = score_task([[[1]], [[9]]], [[[1]], [[2]]])
    assert result["num_exact_matches"] == 1
    assert result["all_exact_match"] is False
    assert result["per_pair_match"] == [True, False]


def test_score_task_length_mismatch_raises():
    try:
        score_task([[[1]]], [[[1]], [[2]]])
        assert False, "expected ValueError"
    except ValueError:
        pass
