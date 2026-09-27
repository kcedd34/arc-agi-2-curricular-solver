"""Applies ADR 0057's pre-registered success/abandonment criteria to a real
pilot result, per docs/decisions/0059-piloto-pretreino-qwen3-base.md.

NOISE_FLOOR_PER_CELL_ACCURACY_GAIN is ADR 0039's measured paired-comparison
gain (+0.0056, baseline_no_pretraining vs warm_started_from_pretraining_v2),
the smallest gain this project has ever observed from cross-task
pretraining and therefore the floor a real signal must clear.
"""
from dataclasses import dataclass

NOISE_FLOOR_PER_CELL_ACCURACY_GAIN = 0.0056
NOISE_FLOOR_MULTIPLE_THRESHOLD = 3.0


@dataclass(frozen=True)
class SuccessCriteriaVerdict:
    has_real_exact_match: bool
    per_cell_accuracy_gain: float
    exceeds_noise_floor_by_multiple: bool
    parse_failure_delta: int
    should_scale: bool


def evaluate_success_criteria(
    baseline_exact_match_count: int,
    warm_started_exact_match_count: int,
    baseline_per_cell_accuracy: float,
    warm_started_per_cell_accuracy: float,
    baseline_parse_failure_count: int,
    warm_started_parse_failure_count: int,
) -> SuccessCriteriaVerdict:
    """A positive parse_failure_delta means warm-started parses more often
    (fewer failures) than baseline, one of ADR 0057's three named criteria."""
    has_real_exact_match = warm_started_exact_match_count > baseline_exact_match_count
    per_cell_accuracy_gain = warm_started_per_cell_accuracy - baseline_per_cell_accuracy
    exceeds_noise_floor_by_multiple = (
        per_cell_accuracy_gain >= NOISE_FLOOR_PER_CELL_ACCURACY_GAIN * NOISE_FLOOR_MULTIPLE_THRESHOLD
    )
    parse_failure_delta = baseline_parse_failure_count - warm_started_parse_failure_count
    should_scale = has_real_exact_match or exceeds_noise_floor_by_multiple or parse_failure_delta > 0
    return SuccessCriteriaVerdict(
        has_real_exact_match=has_real_exact_match,
        per_cell_accuracy_gain=per_cell_accuracy_gain,
        exceeds_noise_floor_by_multiple=exceeds_noise_floor_by_multiple,
        parse_failure_delta=parse_failure_delta,
        should_scale=should_scale,
    )
