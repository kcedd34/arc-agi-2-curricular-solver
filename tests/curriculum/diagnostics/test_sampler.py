"""Tests for the round-1+ rotating sampler (continuous-loop.md Fase A.1)."""
from src.curriculum.diagnostics.sampler import round_sample, stable_shuffle

POOL = [f"task_{i:03d}" for i in range(20)]


def test_stable_shuffle_is_deterministic_across_calls():
    first = stable_shuffle(POOL, seed="x")
    second = stable_shuffle(POOL, seed="x")
    assert first == second
    assert sorted(first) == sorted(POOL)


def test_stable_shuffle_differs_by_seed():
    assert stable_shuffle(POOL, seed="a") != stable_shuffle(POOL, seed="b")


def test_round_sample_is_deterministic():
    first = round_sample(1, window_size=5, pool=POOL)
    second = round_sample(1, window_size=5, pool=POOL)
    assert first == second
    assert len(first) == 5


def test_round_sample_never_exceeds_pool_size():
    sample = round_sample(1, window_size=1000, pool=POOL)
    assert len(sample) == len(POOL)
    assert sorted(sample) == sorted(POOL)


def test_consecutive_rounds_do_not_repeat_the_same_sample():
    round1 = round_sample(1, window_size=5, pool=POOL)
    round2 = round_sample(2, window_size=5, pool=POOL)
    assert round1 != round2


def test_round_sample_empty_pool_returns_empty():
    assert round_sample(1, window_size=5, pool=[]) == []
