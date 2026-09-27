"""First validation-tier run (30-50 tasks, stratified by expected output
grid size, ADR 0015) of the consolidated current config: deterministic
shape constraint (ADR 0025/0026) + geometric_plus_color augmentation
(ADR 0021/0027) + per-attempt conditional decode escalation (ADR 0032).

Reuses per_attempt_conditional_mitigation_pair_diagnostics.py unchanged,
the same module ADR 0032's sanity run used, so this run is on the exact
same code path already validated at sanity tier, just a bigger and
differently-selected sample and color augmentation switched on. See
docs/decisions/0033-consolidated-current-config.md and
docs/decisions/0034-first-validation-consolidated-config.md.

Usage: python -m src.evaluation.run_validation_consolidated_config [training|evaluation] [size]
"""
import sys
from pathlib import Path

from src.evaluation.color_augmentation_configs import build_color_augmentation_configs
from src.evaluation.diagnostic_runner import render_timing_markdown
from src.evaluation.per_attempt_conditional_mitigation_pair_diagnostics import (
    diagnose_task_with_per_attempt_conditional_mitigation,
    render_markdown,
    save_config_rows,
)
from src.evaluation.sample_tiers import select_tier_tasks
from src.evaluation.validation_run_summary import (
    exact_match_rate,
    far_outlier_task_ids,
    per_cell_accuracy_distribution,
    project_time_for_task_count,
)
from src.solvers.neural.model_loader import load_base_model
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "validation_consolidated_config"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations" / "validation_consolidated_config"
CONFIG_NAME = "consolidated_current"
FULL_EVAL_TASK_COUNT = 240


def _consolidated_config():
    configs = dict(build_color_augmentation_configs())
    return configs["geometric_plus_color"]


def _run_all_tasks(base_model, tokenizer, config, tasks, split):
    all_rows = []
    all_timings = []
    for task in tasks.values():
        rows, timing = diagnose_task_with_per_attempt_conditional_mitigation(
            base_model, tokenizer, config, CONFIG_NAME, task, RAW_OUTPUT_ROOT / split,
            enable_conditional_escalation=True,
        )
        save_config_rows(f"validation_consolidated_config_{CONFIG_NAME}_{task.task_id}", rows, OUTPUT_ROOT / split)
        all_rows += rows
        all_timings.append(timing)
    return all_rows, all_timings


def _print_summary(all_rows, all_timings, num_tasks):
    total_seconds = sum(t.total_seconds for t in all_timings)
    print(f"tasks_measured={num_tasks}")
    print(f"exact_match_rate_test={exact_match_rate(all_rows, split='test'):.4f}")
    print(f"per_cell_accuracy_test={per_cell_accuracy_distribution(all_rows, split='test')}")
    print(f"total_seconds={total_seconds:.2f}")
    print(f"avg_seconds_per_task={(total_seconds / num_tasks) if num_tasks else 0.0:.2f}")
    print(f"projected_seconds_240_tasks={project_time_for_task_count(total_seconds, num_tasks, FULL_EVAL_TASK_COUNT):.2f}")
    print(f"far_outlier_tasks={far_outlier_task_ids(all_rows)}")


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    size_override = int(sys.argv[2]) if len(sys.argv) > 2 else None

    config = _consolidated_config()
    base_model, tokenizer = load_base_model(config)
    all_tasks = load_task_set(DATA_ROOT / split)
    tasks = select_tier_tasks(all_tasks, "validation", size_override=size_override)

    all_rows, all_timings = _run_all_tasks(base_model, tokenizer, config, tasks, split)

    print(render_markdown(all_rows))
    print()
    print(render_timing_markdown(all_timings))
    print()
    _print_summary(all_rows, all_timings, len(tasks))


if __name__ == "__main__":
    main()
