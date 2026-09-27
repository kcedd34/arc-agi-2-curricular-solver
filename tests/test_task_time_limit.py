import pytest

from src.evaluation.task_time_limit import (
    NEURAL_TASK_CEILING_SECONDS,
    TaskTimeExceeded,
    TaskTimeLimiter,
    TimeLimitAbortTracker,
)


def _fake_clock(fake_time):
    return lambda: fake_time[0]


def test_ceiling_constant_is_400_seconds():
    assert NEURAL_TASK_CEILING_SECONDS == 400.0


def test_check_does_not_raise_before_ceiling():
    fake_time = [0.0]
    limiter = TaskTimeLimiter(ceiling_seconds=100.0, clock=_fake_clock(fake_time))
    limiter.start()
    fake_time[0] = 50.0
    limiter.check()


def test_check_does_not_raise_exactly_at_ceiling():
    fake_time = [0.0]
    limiter = TaskTimeLimiter(ceiling_seconds=100.0, clock=_fake_clock(fake_time))
    limiter.start()
    fake_time[0] = 100.0
    limiter.check()


def test_check_raises_task_time_exceeded_once_past_ceiling():
    fake_time = [0.0]
    limiter = TaskTimeLimiter(ceiling_seconds=100.0, clock=_fake_clock(fake_time))
    limiter.start()
    fake_time[0] = 100.1
    with pytest.raises(TaskTimeExceeded):
        limiter.check()


def test_elapsed_reflects_clock_delta_since_start():
    fake_time = [10.0]
    limiter = TaskTimeLimiter(ceiling_seconds=100.0, clock=_fake_clock(fake_time))
    limiter.start()
    fake_time[0] = 37.0
    assert limiter.elapsed() == 27.0


def test_deadline_is_start_plus_ceiling():
    fake_time = [10.0]
    limiter = TaskTimeLimiter(ceiling_seconds=100.0, clock=_fake_clock(fake_time))
    limiter.start()
    assert limiter.deadline() == 110.0


def test_abort_tracker_starts_empty():
    tracker = TimeLimitAbortTracker()
    assert tracker.count == 0
    assert tracker.aborted_task_ids == []


def test_abort_tracker_records_and_counts_aborts():
    tracker = TimeLimitAbortTracker()
    tracker.record_abort("264363fd")
    tracker.record_abort("40f6cd08")
    assert tracker.count == 2
    assert tracker.aborted_task_ids == ["264363fd", "40f6cd08"]
