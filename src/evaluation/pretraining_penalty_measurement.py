"""Measures the real pretraining-vs-TTT time penalty on Qwen3-4B-Base,
replacing ADR 0057's OLMo-2-borrowed ratio (2.26x) with a number measured
on this model, at pilot scale, per
docs/decisions/0059-piloto-pretreino-qwen3-base.md.

s/example-epoch = wall_clock_seconds / (num_augmented_examples * num_epochs),
the same formula ADR 0057 section 2 uses for its OLMo-2/Qwen3 reference
table, so results here are directly comparable to that table.
"""
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class RealPenaltyMeasurement:
    pretraining_s_per_example_epoch: float
    mean_ttt_s_per_example_epoch: float
    per_task_ttt_s_per_example_epoch: Dict[str, float]
    real_penalty_ratio: float


@dataclass(frozen=True)
class TimeEstimate:
    task_count: int
    optimistic_seconds: float
    pessimistic_seconds: float


def compute_pretraining_rate(
    pretraining_seconds: float, num_pretraining_augmented_examples: int, pretraining_num_epochs: int
) -> float:
    return pretraining_seconds / (num_pretraining_augmented_examples * pretraining_num_epochs)


def compute_ttt_rate(ttt_seconds: float, num_augmented_examples: int, ttt_num_epochs: int) -> float:
    return ttt_seconds / (num_augmented_examples * ttt_num_epochs)


def compute_real_penalty(
    pretraining_seconds: float,
    num_pretraining_augmented_examples: int,
    pretraining_num_epochs: int,
    per_task_ttt_seconds: Dict[str, float],
    per_task_num_augmented_examples: Dict[str, int],
    ttt_num_epochs: int,
) -> RealPenaltyMeasurement:
    """per_task_ttt_seconds/per_task_num_augmented_examples share the same
    task_id keys, one entry per paired evaluation task (ADR 0039 design)."""
    pretraining_rate = compute_pretraining_rate(
        pretraining_seconds, num_pretraining_augmented_examples, pretraining_num_epochs
    )
    per_task_rates = {
        task_id: compute_ttt_rate(seconds, per_task_num_augmented_examples[task_id], ttt_num_epochs)
        for task_id, seconds in per_task_ttt_seconds.items()
    }
    mean_ttt_rate = sum(per_task_rates.values()) / len(per_task_rates)
    return RealPenaltyMeasurement(
        pretraining_s_per_example_epoch=pretraining_rate,
        mean_ttt_s_per_example_epoch=mean_ttt_rate,
        per_task_ttt_s_per_example_epoch=per_task_rates,
        real_penalty_ratio=pretraining_rate / mean_ttt_rate,
    )


def recalculate_time_estimate(
    task_count: int,
    mean_examples_per_task: float,
    ttt_num_epochs: int,
    min_ttt_s_per_example_epoch: float,
    max_ttt_s_per_example_epoch: float,
    real_penalty_ratio: float,
) -> TimeEstimate:
    """Mirrors ADR 0057 section 2's own range methodology (the measured
    per-task TTT rate spread, scaled by the pretraining-vs-TTT penalty) but
    with this pilot's real, measured real_penalty_ratio in place of
    OLMo-2's borrowed 2.26x.
    """
    total_example_epochs = task_count * mean_examples_per_task * ttt_num_epochs
    return TimeEstimate(
        task_count=task_count,
        optimistic_seconds=total_example_epochs * min_ttt_s_per_example_epoch * real_penalty_ratio,
        pessimistic_seconds=total_example_epochs * max_ttt_s_per_example_epoch * real_penalty_ratio,
    )
