"""Cross-task pretraining pilot v3: 100-150 task scale, circuit breaker,
and real Qwen3-4B-Base pretraining-vs-TTT penalty measurement (ADR 0057),
see docs/decisions/0059-piloto-pretreino-qwen3-base.md.

Builds directly on run_cross_task_pretraining_pilot_v2.py's design (same
paired baseline-vs-warm-started comparison over the same reserved-eval
subsample mechanism, ADR 0039), adding two things ADR 0057's borrowed
estimate range was missing:

- A per-task TaskTimeLimiter/TimeLimitAbortTracker (ADR 0049/0058), wired
  the same way as run_circuit_breaker_smoke.py, so a single runaway task
  (the 264363fd/0934a4d8-class outlier) cannot stall this larger run.
- Real pretraining-vs-TTT rate measurement
  (pretraining_penalty_measurement.py) replacing ADR 0057's OLMo-2-
  borrowed 2.26x ratio, plus ADR 0057's pre-registered success/
  abandonment criteria (pretraining_success_criteria.py) applied to this
  run's own paired result.

Usage: python -m src.evaluation.run_cross_task_pretraining_pilot_v3 [pretraining_size] [eval_size]
"""
import random
import statistics
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Tuple

from src.evaluation.color_augmentation_configs import build_color_augmentation_configs
from src.evaluation.diagnostic_runner import TimingRow, render_timing_markdown
from src.evaluation.per_attempt_conditional_mitigation_pair_diagnostics import (
    PerAttemptConditionalMitigationPairRow,
    diagnose_task_with_per_attempt_conditional_mitigation,
    render_markdown,
    save_config_rows,
)
from src.evaluation.pretraining_penalty_measurement import compute_real_penalty, recalculate_time_estimate
from src.evaluation.pretraining_split import save_split_manifest, select_pretraining_tasks_excluding_reserved
from src.evaluation.pretraining_success_criteria import evaluate_success_criteria
from src.evaluation.reserved_evaluation_tasks import reserved_evaluation_task_ids
from src.evaluation.task_time_limit import (
    NEURAL_TASK_CEILING_SECONDS,
    TaskTimeExceeded,
    TaskTimeLimiter,
    TimeLimitAbortTracker,
)
from src.evaluation.validation_run_summary import exact_match_rate, per_cell_accuracy_distribution
from src.solvers.neural.checkpoint_utils import find_resumable_checkpoint
from src.solvers.neural.cross_task_pretraining import pretrain_shared_adapter
from src.solvers.neural.ttt_trainer import count_augmented_training_examples
from src.utils.task_loader import Task, load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "cross_task_pretraining_pilot_v3"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations" / "cross_task_pretraining_pilot_v3"
ADAPTER_DIR = str(PROJECT_ROOT / "outputs" / "adapters" / "cross_task_pretrained_v3")
PRETRAINING_SPLIT_MANIFEST_PATH = OUTPUT_ROOT / "pretraining_split_v3.json"
EVAL_SPLIT_MANIFEST_PATH = OUTPUT_ROOT / "eval_subsample_v3.json"
PRETRAINING_CHECKPOINT_DIR = str(PROJECT_ROOT / "outputs" / "ttt_tmp" / "cross_task_pretraining_pilot_v3")

DEFAULT_PRETRAINING_TASK_COUNT = 120
DEFAULT_EVAL_TASK_COUNT = 12
EVAL_SUBSAMPLE_SEED = 4242
TIMING_OUTLIER_MULTIPLIER = 5.0
TIMING_OUTLIER_MAJORITY_FRACTION = 0.5
PRODUCTION_TASK_COUNTS = (400, 600)

BASELINE_CONFIG_NAME = "baseline_no_pretraining"
WARM_START_CONFIG_NAME = "warm_started_from_pretraining_v3"


def _consolidated_config():
    configs = dict(build_color_augmentation_configs())
    return configs["geometric_plus_color"]


def _select_pretraining_tasks(size: int) -> Dict[str, Task]:
    training_tasks = load_task_set(DATA_ROOT / "training")
    reserved_ids = reserved_evaluation_task_ids()
    selected = select_pretraining_tasks_excluding_reserved(training_tasks, size, reserved_ids)
    save_split_manifest(list(selected), PRETRAINING_SPLIT_MANIFEST_PATH)
    return selected


def _seeded_subsample(sorted_ids: List[str], size: int, seed: int) -> List[str]:
    return sorted(random.Random(seed).sample(sorted_ids, min(size, len(sorted_ids))))


def _select_eval_subsample(size: int) -> Dict[str, Task]:
    """Seeded subsample of ADR 0036's reserved 44-task pool, not a
    redefinition of which tasks count as reserved."""
    evaluation_tasks_pool = load_task_set(DATA_ROOT / "evaluation")
    reserved_ids = sorted(reserved_evaluation_task_ids())
    chosen_ids = _seeded_subsample(reserved_ids, size, EVAL_SUBSAMPLE_SEED)
    save_split_manifest(chosen_ids, EVAL_SPLIT_MANIFEST_PATH)
    return {task_id: evaluation_tasks_pool[task_id] for task_id in chosen_ids}


def _run_pretraining_phase(base_model, tokenizer, config, pretraining_tasks: Dict[str, Task]) -> float:
    # Lazy import: unsloth only exists in the WSL GPU venv, not on the host
    # Python used for the pure-logic test suite (same boundary as ADR 0023).
    from src.solvers.neural.lora_setup import attach_fresh_lora, detach_lora

    # Same "steps" strategy as ADR 0036/0039, reused unmodified; a fresh
    # checkpoint dir/adapter dir so this larger run never mixes with or
    # overwrites the v2 pilot's own checkpoint/adapter.
    pretraining_config = replace(
        config, checkpoint_output_dir=PRETRAINING_CHECKPOINT_DIR,
        checkpoint_save_strategy="steps", checkpoint_save_steps=500,
    )
    model = attach_fresh_lora(base_model, config)
    resume_from = find_resumable_checkpoint(PRETRAINING_CHECKPOINT_DIR)
    start = time.monotonic()
    model = pretrain_shared_adapter(model, tokenizer, pretraining_tasks, pretraining_config, resume_from_checkpoint=resume_from)
    pretraining_seconds = time.monotonic() - start
    model.save_pretrained(ADAPTER_DIR)
    detach_lora(model)
    return pretraining_seconds


def _run_scenario(base_model, tokenizer, config, eval_tasks: Dict[str, Task], config_name: str, adapter_dir) -> Tuple[List[PerAttemptConditionalMitigationPairRow], List[TimingRow], TimeLimitAbortTracker]:
    """Same per-task loop as run_cross_task_pretraining_pilot_v2.py, plus
    the circuit breaker wiring confirmed on real GPU hardware by ADR 0058's
    run_circuit_breaker_smoke.py: one TaskTimeLimiter per task, aborted
    tasks recorded and skipped rather than stalling the whole scenario."""
    all_rows: List[PerAttemptConditionalMitigationPairRow] = []
    all_timings: List[TimingRow] = []
    aborts = TimeLimitAbortTracker()
    for task in eval_tasks.values():
        limiter = TaskTimeLimiter(ceiling_seconds=NEURAL_TASK_CEILING_SECONDS)
        limiter.start()
        try:
            rows, timing = diagnose_task_with_per_attempt_conditional_mitigation(
                base_model, tokenizer, config, config_name, task,
                RAW_OUTPUT_ROOT / config_name, enable_conditional_escalation=True,
                adapter_dir=adapter_dir, limiter=limiter,
            )
        except TaskTimeExceeded:
            aborts.record_abort(task.task_id)
            print(f"[ABORTED BY CIRCUIT BREAKER] task={task.task_id} elapsed={limiter.elapsed():.2f}s")
            continue
        save_config_rows(f"{config_name}_{task.task_id}", rows, OUTPUT_ROOT / config_name)
        all_rows += rows
        all_timings.append(timing)
    print(f"[{config_name}] tasks aborted by circuit breaker: {sorted(aborts.aborted_task_ids)}")
    return all_rows, all_timings, aborts


def _flag_timing_outliers(timings: List[TimingRow]) -> List[str]:
    """Monitors, but does not halt for, ADR 0036's documented rare timing
    anomaly: flags tasks running TIMING_OUTLIER_MULTIPLIER times the
    sample median, and separately warns (without stopping) only if a
    majority of tasks are flagged, per explicit user instruction. The
    per-task circuit breaker (NEURAL_TASK_CEILING_SECONDS) already bounds
    the worst case this watches for; this stays a softer, earlier signal."""
    if len(timings) < 2:
        return []
    median_seconds = statistics.median(t.total_seconds for t in timings)
    flagged = [t.task_id for t in timings if t.total_seconds > TIMING_OUTLIER_MULTIPLIER * median_seconds]
    if flagged:
        print(f"[timing anomaly watch] median={median_seconds:.2f}s, flagged tasks (>{TIMING_OUTLIER_MULTIPLIER}x median): {flagged}")
    if len(flagged) / len(timings) > TIMING_OUTLIER_MAJORITY_FRACTION:
        print("[timing anomaly watch] WARNING: majority of tasks flagged, not just 1-2 isolated cases.")
    return flagged


def _print_scenario_summary(label: str, rows, timings: List[TimingRow]) -> None:
    total_seconds = sum(t.total_seconds for t in timings)
    distribution = per_cell_accuracy_distribution(rows, split="test")
    print(f"[{label}] exact_match_rate_test={exact_match_rate(rows, split='test'):.4f}")
    print(f"[{label}] per_cell_accuracy_test={distribution}")
    print(f"[{label}] ttt_total_seconds={total_seconds:.2f}")
    _flag_timing_outliers(timings)


def _measure_real_penalty(config, pretraining_tasks: Dict[str, Task], pretraining_seconds: float, eval_tasks: Dict[str, Task], baseline_timings: List[TimingRow]):
    """num_pretraining_augmented_examples mirrors
    cross_task_pretraining.build_cross_task_corpus's own example count
    (sum of count_augmented_training_examples over the same task pool,
    shuffling does not change the count); per_task_ttt_seconds comes from
    the baseline scenario's own TimingRow.ttt_seconds, one entry per
    eval task that was NOT aborted by the circuit breaker."""
    num_pretraining_augmented_examples = sum(
        count_augmented_training_examples(task, config) for task in pretraining_tasks.values()
    )
    per_task_ttt_seconds = {t.task_id: t.ttt_seconds for t in baseline_timings}
    per_task_num_augmented_examples = {
        task_id: count_augmented_training_examples(eval_tasks[task_id], config)
        for task_id in per_task_ttt_seconds
    }
    return compute_real_penalty(
        pretraining_seconds=pretraining_seconds,
        num_pretraining_augmented_examples=num_pretraining_augmented_examples,
        pretraining_num_epochs=config.pretraining_num_epochs,
        per_task_ttt_seconds=per_task_ttt_seconds,
        per_task_num_augmented_examples=per_task_num_augmented_examples,
        ttt_num_epochs=config.ttt_num_epochs,
    )


def _recalculate_production_estimates(config, pretraining_tasks: Dict[str, Task], real_penalty):
    """Mirrors ADR 0057's own range methodology (min/max measured TTT
    rate scaled by the pretraining-vs-TTT penalty) for both edges of the
    400-600 production range, using this pilot's real, measured
    real_penalty_ratio in place of OLMo-2's borrowed 2.26x."""
    mean_examples_per_task = statistics.mean(
        count_augmented_training_examples(task, config) for task in pretraining_tasks.values()
    )
    rates = list(real_penalty.per_task_ttt_s_per_example_epoch.values())
    return [
        recalculate_time_estimate(
            task_count=task_count,
            mean_examples_per_task=mean_examples_per_task,
            ttt_num_epochs=config.ttt_num_epochs,
            min_ttt_s_per_example_epoch=min(rates),
            max_ttt_s_per_example_epoch=max(rates),
            real_penalty_ratio=real_penalty.real_penalty_ratio,
        )
        for task_count in PRODUCTION_TASK_COUNTS
    ]


def _exact_match_count(rows, split: str = "test") -> int:
    return sum(1 for r in rows if r.split == split and r.constrained_exact_match)


def _mean_per_cell_accuracy(rows, split: str = "test") -> float:
    distribution = per_cell_accuracy_distribution(rows, split=split)
    return distribution["mean"] if distribution["mean"] is not None else 0.0


def _parse_failure_count(rows, split: str = "test") -> int:
    """A total parse failure is a pair with no measurable accuracy at
    all (constrained_best_cell_accuracy is None), the same "far" case
    per_cell_accuracy_distribution's _band already treats as worst-case,
    and the same definition ADR 0039 used for its own 5-pair count."""
    return sum(1 for r in rows if r.split == split and r.constrained_best_cell_accuracy is None)


def main() -> None:
    # Lazy import: unsloth only exists in the WSL GPU venv, not on the host
    # Python used for the pure-logic test suite (same boundary as ADR 0023).
    from src.solvers.neural.model_loader import load_base_model

    pretraining_size = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PRETRAINING_TASK_COUNT
    eval_size = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_EVAL_TASK_COUNT

    config = _consolidated_config()
    base_model, tokenizer = load_base_model(config)

    eval_tasks = _select_eval_subsample(eval_size)

    baseline_rows, baseline_timings, _ = _run_scenario(base_model, tokenizer, config, eval_tasks, BASELINE_CONFIG_NAME, adapter_dir=None)
    print(render_markdown(baseline_rows))
    print(render_timing_markdown(baseline_timings))
    _print_scenario_summary(BASELINE_CONFIG_NAME, baseline_rows, baseline_timings)

    pretraining_tasks = _select_pretraining_tasks(pretraining_size)
    pretraining_seconds = _run_pretraining_phase(base_model, tokenizer, config, pretraining_tasks)
    print(f"pretraining_tasks={len(pretraining_tasks)}")
    print(f"pretraining_seconds={pretraining_seconds:.2f}")

    warm_rows, warm_timings, _ = _run_scenario(base_model, tokenizer, config, eval_tasks, WARM_START_CONFIG_NAME, adapter_dir=ADAPTER_DIR)
    print(render_markdown(warm_rows))
    print(render_timing_markdown(warm_timings))
    _print_scenario_summary(WARM_START_CONFIG_NAME, warm_rows, warm_timings)

    real_penalty = _measure_real_penalty(config, pretraining_tasks, pretraining_seconds, eval_tasks, baseline_timings)
    print(f"real_penalty_ratio={real_penalty.real_penalty_ratio:.4f}")
    print(f"pretraining_s_per_example_epoch={real_penalty.pretraining_s_per_example_epoch:.4f}")
    print(f"mean_ttt_s_per_example_epoch={real_penalty.mean_ttt_s_per_example_epoch:.4f}")

    for estimate in _recalculate_production_estimates(config, pretraining_tasks, real_penalty):
        print(
            f"recalculated_estimate task_count={estimate.task_count} "
            f"optimistic_hours={estimate.optimistic_seconds / 3600:.2f} "
            f"pessimistic_hours={estimate.pessimistic_seconds / 3600:.2f}"
        )

    verdict = evaluate_success_criteria(
        baseline_exact_match_count=_exact_match_count(baseline_rows),
        warm_started_exact_match_count=_exact_match_count(warm_rows),
        baseline_per_cell_accuracy=_mean_per_cell_accuracy(baseline_rows),
        warm_started_per_cell_accuracy=_mean_per_cell_accuracy(warm_rows),
        baseline_parse_failure_count=_parse_failure_count(baseline_rows),
        warm_started_parse_failure_count=_parse_failure_count(warm_rows),
    )
    print(f"success_criteria_verdict={verdict}")


if __name__ == "__main__":
    main()
