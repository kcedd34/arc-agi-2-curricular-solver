"""Cross-task pretraining pilot v2: smaller scale, paired comparison
(ADR 0022/0035/0036), see docs/decisions/0039-piloto-pretreino-v2-comparacao-pareada.md.

ADR 0036's ~150-task pretraining/~44-task evaluation pilot spent ~7h and
still could not answer the accuracy question (only 3/44 reserved tasks were
measured before a deliberate interruption). This script reruns the same
hypothesis at a scale designed to finish and to answer it validly:

- Pretraining: reuses pretraining_split.select_pretraining_tasks_excluding_reserved
  (same seed/disjointness mechanism as ADR 0036), just with a smaller
  `pretraining_size` (~40, not 150).
- Evaluation: reuses reserved_evaluation_tasks.reserved_evaluation_task_ids
  (the same 44-task reserved pool ADR 0036 drew from), then takes one
  seeded subsample of ~10-12 tasks from it.
- Paired comparison: the *same* eval subsample is run under two scenarios,
  baseline (no adapter, ADR 0034/0037's exact config) and warm-started
  (this run's own freshly-trained pretraining adapter) - this is what lets
  a per-cell-accuracy/close-vs-far difference be attributed to the
  adapter, rather than to two different task samples (the ADR 0034
  validation-tier 30% vs. sanity-tier 12.5% far-rate confound this design
  is meant to avoid).

Checkpointing (ADR 0036) is reused unmodified; the timing anomaly ADR 0036
named as a documented rare risk is monitored (_flag_timing_outliers) but
does not halt the run unless it affects most tasks.

Usage: python -m src.evaluation.run_cross_task_pretraining_pilot_v2 [pretraining_size] [eval_size]
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
from src.evaluation.pretraining_split import save_split_manifest, select_pretraining_tasks_excluding_reserved
from src.evaluation.reserved_evaluation_tasks import reserved_evaluation_task_ids
from src.evaluation.validation_run_summary import exact_match_rate, per_cell_accuracy_distribution
from src.solvers.neural.checkpoint_utils import find_resumable_checkpoint
from src.solvers.neural.cross_task_pretraining import pretrain_shared_adapter
from src.utils.task_loader import Task, load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "cross_task_pretraining_pilot_v2"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations" / "cross_task_pretraining_pilot_v2"
ADAPTER_DIR = str(PROJECT_ROOT / "outputs" / "adapters" / "cross_task_pretrained_v2")
PRETRAINING_SPLIT_MANIFEST_PATH = OUTPUT_ROOT / "pretraining_split_v2.json"
EVAL_SPLIT_MANIFEST_PATH = OUTPUT_ROOT / "eval_subsample_v2.json"
PRETRAINING_CHECKPOINT_DIR = str(PROJECT_ROOT / "outputs" / "ttt_tmp" / "cross_task_pretraining_pilot_v2")

DEFAULT_PRETRAINING_TASK_COUNT = 40
DEFAULT_EVAL_TASK_COUNT = 12
EVAL_SUBSAMPLE_SEED = 4242
TIMING_OUTLIER_MULTIPLIER = 5.0
TIMING_OUTLIER_MAJORITY_FRACTION = 0.5

BASELINE_CONFIG_NAME = "baseline_no_pretraining"
WARM_START_CONFIG_NAME = "warm_started_from_pretraining_v2"


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

    # Same "steps" strategy as ADR 0036, reused unmodified; a fresh
    # checkpoint dir/adapter dir so this smaller run never mixes with or
    # overwrites ADR 0036's own 150-task checkpoint/adapter.
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


def _run_scenario(base_model, tokenizer, config, eval_tasks: Dict[str, Task], config_name: str, adapter_dir) -> Tuple[List[PerAttemptConditionalMitigationPairRow], List[TimingRow]]:
    all_rows: List[PerAttemptConditionalMitigationPairRow] = []
    all_timings: List[TimingRow] = []
    for task in eval_tasks.values():
        rows, timing = diagnose_task_with_per_attempt_conditional_mitigation(
            base_model, tokenizer, config, config_name, task,
            RAW_OUTPUT_ROOT / config_name, enable_conditional_escalation=True,
            adapter_dir=adapter_dir,
        )
        save_config_rows(f"{config_name}_{task.task_id}", rows, OUTPUT_ROOT / config_name)
        all_rows += rows
        all_timings.append(timing)
    return all_rows, all_timings


def _flag_timing_outliers(timings: List[TimingRow]) -> List[str]:
    """Monitors, but does not halt for, ADR 0036's documented rare timing
    anomaly: flags tasks running TIMING_OUTLIER_MULTIPLIER times the
    sample median, and separately warns (without stopping) only if a
    majority of tasks are flagged, per explicit user instruction."""
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


def main() -> None:
    # Lazy import: unsloth only exists in the WSL GPU venv, not on the host
    # Python used for the pure-logic test suite (same boundary as ADR 0023).
    from src.solvers.neural.model_loader import load_base_model

    pretraining_size = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PRETRAINING_TASK_COUNT
    eval_size = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_EVAL_TASK_COUNT

    config = _consolidated_config()
    base_model, tokenizer = load_base_model(config)

    eval_tasks = _select_eval_subsample(eval_size)

    baseline_rows, baseline_timings = _run_scenario(base_model, tokenizer, config, eval_tasks, BASELINE_CONFIG_NAME, adapter_dir=None)
    print(render_markdown(baseline_rows))
    print(render_timing_markdown(baseline_timings))
    _print_scenario_summary(BASELINE_CONFIG_NAME, baseline_rows, baseline_timings)

    pretraining_tasks = _select_pretraining_tasks(pretraining_size)
    pretraining_seconds = _run_pretraining_phase(base_model, tokenizer, config, pretraining_tasks)
    print(f"pretraining_tasks={len(pretraining_tasks)}")
    print(f"pretraining_seconds={pretraining_seconds:.2f}")

    warm_rows, warm_timings = _run_scenario(base_model, tokenizer, config, eval_tasks, WARM_START_CONFIG_NAME, adapter_dir=ADAPTER_DIR)
    print(render_markdown(warm_rows))
    print(render_timing_markdown(warm_timings))
    _print_scenario_summary(WARM_START_CONFIG_NAME, warm_rows, warm_timings)


if __name__ == "__main__":
    main()
