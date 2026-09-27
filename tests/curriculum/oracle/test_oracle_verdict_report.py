from src.curriculum.oracle.report import summarize, summary_lines
from src.curriculum.oracle.verdict import Verdict


def _v(task_id, train, test, error=None):
    return Verdict(task_id, 1.0, train, test, train > 0, test > 0, "", error)


def test_summary_counts_three_numbers_and_crashes():
    verdicts = [_v("a", 0, 0), _v("b", 3, 0), _v("c", 2, 2), _v("d", 0, 0, "Boom: x")]
    summary = summarize(verdicts)
    assert (summary["explain_train"], summary["explain_train_and_test"], summary["explain_nothing"]) == (2, 1, 1)
    assert summary["crashed"] == ["d"] and summary["ceiling_task_ids"] == ["c"]


def test_summary_lines_fit_the_terminal_budget():
    assert len(summary_lines(summarize([_v("a", 1, 1)]))) <= 14
