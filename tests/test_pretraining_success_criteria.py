import pytest

from src.evaluation.pretraining_success_criteria import (
    NOISE_FLOOR_PER_CELL_ACCURACY_GAIN,
    NOISE_FLOOR_MULTIPLE_THRESHOLD,
    evaluate_success_criteria,
)


def _base_kwargs():
    return dict(
        baseline_exact_match_count=0,
        warm_started_exact_match_count=0,
        baseline_per_cell_accuracy=0.80,
        warm_started_per_cell_accuracy=0.80,
        baseline_parse_failure_count=5,
        warm_started_parse_failure_count=5,
    )


def test_all_flat_criteria_do_not_scale():
    verdict = evaluate_success_criteria(**_base_kwargs())
    assert verdict.has_real_exact_match is False
    assert verdict.exceeds_noise_floor_by_multiple is False
    assert verdict.parse_failure_delta == 0
    assert verdict.should_scale is False


def test_real_exact_match_alone_triggers_should_scale():
    kwargs = _base_kwargs()
    kwargs["warm_started_exact_match_count"] = 1
    verdict = evaluate_success_criteria(**kwargs)
    assert verdict.has_real_exact_match is True
    assert verdict.should_scale is True


def test_per_cell_gain_below_noise_floor_multiple_does_not_scale():
    kwargs = _base_kwargs()
    kwargs["warm_started_per_cell_accuracy"] = kwargs["baseline_per_cell_accuracy"] + NOISE_FLOOR_PER_CELL_ACCURACY_GAIN
    verdict = evaluate_success_criteria(**kwargs)
    assert verdict.exceeds_noise_floor_by_multiple is False
    assert verdict.should_scale is False


def test_per_cell_gain_at_exactly_the_multiple_threshold_scales():
    kwargs = _base_kwargs()
    gain = NOISE_FLOOR_PER_CELL_ACCURACY_GAIN * NOISE_FLOOR_MULTIPLE_THRESHOLD
    kwargs["warm_started_per_cell_accuracy"] = kwargs["baseline_per_cell_accuracy"] + gain
    verdict = evaluate_success_criteria(**kwargs)
    assert verdict.per_cell_accuracy_gain == pytest.approx(gain)
    assert verdict.exceeds_noise_floor_by_multiple is True
    assert verdict.should_scale is True


def test_fewer_parse_failures_in_warm_started_triggers_should_scale():
    kwargs = _base_kwargs()
    kwargs["warm_started_parse_failure_count"] = 2
    verdict = evaluate_success_criteria(**kwargs)
    assert verdict.parse_failure_delta == 3
    assert verdict.should_scale is True


def test_more_parse_failures_in_warm_started_does_not_scale_on_its_own():
    kwargs = _base_kwargs()
    kwargs["warm_started_parse_failure_count"] = 8
    verdict = evaluate_success_criteria(**kwargs)
    assert verdict.parse_failure_delta == -3
    assert verdict.should_scale is False


def test_per_cell_accuracy_gain_can_be_negative():
    kwargs = _base_kwargs()
    kwargs["warm_started_per_cell_accuracy"] = 0.70
    verdict = evaluate_success_criteria(**kwargs)
    assert verdict.per_cell_accuracy_gain == pytest.approx(-0.10)
    assert verdict.exceeds_noise_floor_by_multiple is False
