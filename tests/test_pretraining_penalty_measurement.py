import pytest

from src.evaluation.pretraining_penalty_measurement import (
    compute_pretraining_rate,
    compute_ttt_rate,
    compute_real_penalty,
    recalculate_time_estimate,
)


def test_compute_pretraining_rate_divides_seconds_by_examples_times_epochs():
    rate = compute_pretraining_rate(
        pretraining_seconds=1000.0, num_pretraining_augmented_examples=100, pretraining_num_epochs=2
    )
    assert rate == pytest.approx(5.0)


def test_compute_ttt_rate_divides_seconds_by_examples_times_epochs():
    rate = compute_ttt_rate(ttt_seconds=48.0, num_augmented_examples=24, ttt_num_epochs=2)
    assert rate == pytest.approx(1.0)


def test_compute_real_penalty_averages_per_task_ttt_rates():
    result = compute_real_penalty(
        pretraining_seconds=1000.0,
        num_pretraining_augmented_examples=100,
        pretraining_num_epochs=2,
        per_task_ttt_seconds={"task_a": 48.0, "task_b": 24.0},
        per_task_num_augmented_examples={"task_a": 24, "task_b": 24},
        ttt_num_epochs=2,
    )
    assert result.pretraining_s_per_example_epoch == pytest.approx(5.0)
    assert result.per_task_ttt_s_per_example_epoch == {"task_a": pytest.approx(1.0), "task_b": pytest.approx(0.5)}
    assert result.mean_ttt_s_per_example_epoch == pytest.approx(0.75)
    assert result.real_penalty_ratio == pytest.approx(5.0 / 0.75)


def test_compute_real_penalty_with_single_task_matches_that_tasks_own_rate():
    result = compute_real_penalty(
        pretraining_seconds=200.0,
        num_pretraining_augmented_examples=50,
        pretraining_num_epochs=1,
        per_task_ttt_seconds={"only_task": 20.0},
        per_task_num_augmented_examples={"only_task": 10},
        ttt_num_epochs=1,
    )
    assert result.mean_ttt_s_per_example_epoch == pytest.approx(2.0)
    assert result.real_penalty_ratio == pytest.approx(2.0)


def test_recalculate_time_estimate_optimistic_uses_min_rate():
    estimate = recalculate_time_estimate(
        task_count=100,
        mean_examples_per_task=10.0,
        ttt_num_epochs=2,
        min_ttt_s_per_example_epoch=0.5,
        max_ttt_s_per_example_epoch=1.5,
        real_penalty_ratio=2.0,
    )
    total_example_epochs = 100 * 10.0 * 2
    assert estimate.task_count == 100
    assert estimate.optimistic_seconds == pytest.approx(total_example_epochs * 0.5 * 2.0)
    assert estimate.pessimistic_seconds == pytest.approx(total_example_epochs * 1.5 * 2.0)


def test_recalculate_time_estimate_pessimistic_is_never_smaller_than_optimistic():
    estimate = recalculate_time_estimate(
        task_count=500,
        mean_examples_per_task=20.0,
        ttt_num_epochs=3,
        min_ttt_s_per_example_epoch=0.4,
        max_ttt_s_per_example_epoch=1.2,
        real_penalty_ratio=2.26,
    )
    assert estimate.pessimistic_seconds >= estimate.optimistic_seconds
