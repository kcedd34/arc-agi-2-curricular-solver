from src.evaluation.run_cross_task_pretraining_pilot_v2 import _flag_timing_outliers, _seeded_subsample
from src.evaluation.diagnostic_runner import TimingRow


def _fake_ids(n: int) -> list:
    return [f"task_{i:04d}" for i in range(n)]


def test_seeded_subsample_is_deterministic_for_a_fixed_seed():
    ids = _fake_ids(44)
    first = _seeded_subsample(ids, size=12, seed=4242)
    second = _seeded_subsample(ids, size=12, seed=4242)
    assert first == second


def test_seeded_subsample_respects_requested_size():
    ids = _fake_ids(44)
    assert len(_seeded_subsample(ids, size=12, seed=4242)) == 12


def test_seeded_subsample_caps_at_available_population():
    ids = _fake_ids(5)
    assert len(_seeded_subsample(ids, size=12, seed=4242)) == 5


def test_seeded_subsample_different_seeds_give_different_samples():
    ids = _fake_ids(44)
    a = _seeded_subsample(ids, size=12, seed=1)
    b = _seeded_subsample(ids, size=12, seed=2)
    assert a != b


def _fake_timing(task_id: str, total_seconds: float) -> TimingRow:
    return TimingRow(config_name="cfg", task_id=task_id, ttt_seconds=total_seconds, total_seconds=total_seconds)


def test_flag_timing_outliers_flags_only_far_above_median():
    timings = [_fake_timing(f"t{i}", 100.0) for i in range(5)] + [_fake_timing("slow", 5000.0)]
    flagged = _flag_timing_outliers(timings)
    assert flagged == ["slow"]


def test_flag_timing_outliers_flags_nothing_when_all_similar():
    timings = [_fake_timing(f"t{i}", 100.0 + i) for i in range(6)]
    assert _flag_timing_outliers(timings) == []


def test_flag_timing_outliers_empty_on_single_task():
    assert _flag_timing_outliers([_fake_timing("only", 100.0)]) == []
