from src.evaluation.task_selector import parse_task_selector


def test_parse_task_selector_with_integer_limit():
    limit, task_ids = parse_task_selector("2")
    assert limit == 2
    assert task_ids is None


def test_parse_task_selector_with_single_task_id():
    limit, task_ids = parse_task_selector("136b0064")
    assert limit is None
    assert task_ids == ["136b0064"]


def test_parse_task_selector_with_multiple_task_ids():
    limit, task_ids = parse_task_selector("136b0064,135a2760")
    assert limit is None
    assert task_ids == ["136b0064", "135a2760"]
