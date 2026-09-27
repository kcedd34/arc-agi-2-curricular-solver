"""RN-CUR-38: timing statistics carry median, slowest task id and per-task times."""
from src.curriculum.timing import TimedResult, summarize_durations, summarize_timing
from src.curriculum.timing_report import timing_line, write_task_times


def test_summarize_durations_reports_mean_median_max_and_slowest_id():
    timing = summarize_durations({"a": 1.0, "b": 2.0, "c": 300.0}, wall_seconds=50.0)
    assert timing.median_task_seconds == 2.0
    assert timing.max_task_seconds == 300.0
    assert timing.slowest_task_id == "c"
    assert abs(timing.mean_task_seconds - 101.0) < 1e-9


def test_even_count_median_averages_the_middle_pair():
    assert summarize_durations({"a": 1.0, "b": 3.0}, 1.0).median_task_seconds == 2.0


def test_summarize_timing_skips_errored_items():
    outcomes = [("a", TimedResult("x", 4.0)), ("b", RuntimeError("boom"))]
    timing = summarize_timing(outcomes, wall_seconds=4.0)
    assert timing.num_timed == 1 and timing.per_task_seconds == {"a": 4.0}


def test_empty_durations_do_not_crash_and_line_renders():
    assert "n=0" in timing_line(summarize_durations({}, 0.0))


def test_write_task_times_lists_slowest_first(tmp_path):
    path = write_task_times(tmp_path / "t.json", summarize_durations({"a": 1.0, "b": 9.0}, 1.0))
    assert list(__import__("json").loads(path.read_text())["per_task_seconds"]) == ["b", "a"]
