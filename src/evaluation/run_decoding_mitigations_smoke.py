"""Smoke-tier test of the two decoding mitigations for the failure modes
diagnosed in docs/decisions/0028-timing-anomaly-and-task-complexity-investigation.md:
repetition_penalty/no_repeat_ngram_size for 13e47133's degenerate
repetition, and a stop-on-second-Input heuristic for 0934a4d8's
hallucinated second example.

Primary comparison: the two affected tasks (0934a4d8, 13e47133) under all
four configs (baseline, repetition_only, stop_heuristic_only, both), to
read each mitigation's isolated and combined effect.

Regression check: the other 6 tasks from the same sanity-tier sample
(ADR 0017/0023/0024/0026/0027/0028), under baseline and both only, since
those tasks never showed either failure mode and the question there is
only whether the combined mitigation state (the production candidate)
changes their behavior, not each mitigation's individual contribution.

Usage: python -m src.evaluation.run_decoding_mitigations_smoke [training|evaluation]

Diagnostic only, does not decide production-default status, see
docs/decisions/0029-decoding-mitigations-repetition-hallucination.md.
"""
import sys
from pathlib import Path

from src.evaluation.decoding_mitigation_configs import build_decoding_mitigation_configs
from src.evaluation.diagnostic_runner import render_timing_markdown
from src.evaluation.mitigation_diagnostics import diagnose_task_with_mitigations, render_markdown, save_config_rows
from src.evaluation.sample_tiers import select_tier_tasks
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.model_loader import load_base_model
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "decoding_mitigations_smoke"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations" / "decoding_mitigations_smoke"

ANOMALY_TASK_IDS = ["0934a4d8", "13e47133"]
REGRESSION_CONFIG_NAMES = {"baseline", "both"}


def _run_task_under_configs(base_model, tokenizer, task, configs, split):
    all_rows = []
    all_timings = []
    for config_name, config in configs:
        rows, timing = diagnose_task_with_mitigations(
            base_model, tokenizer, config, config_name, task, RAW_OUTPUT_ROOT / split
        )
        save_config_rows(f"decoding_mitigations_smoke_{config_name}_{task.task_id}", rows, OUTPUT_ROOT / split)
        all_rows += rows
        all_timings.append(timing)
    return all_rows, all_timings


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    base_model, tokenizer = load_base_model(NeuralSolverConfig())
    all_tasks = load_task_set(DATA_ROOT / split)
    sanity_tasks = select_tier_tasks(all_tasks, "sanity")

    anomaly_tasks = {task_id: sanity_tasks[task_id] for task_id in ANOMALY_TASK_IDS}
    regression_tasks = {tid: t for tid, t in sanity_tasks.items() if tid not in ANOMALY_TASK_IDS}
    all_configs = build_decoding_mitigation_configs()
    regression_configs = [(name, cfg) for name, cfg in all_configs if name in REGRESSION_CONFIG_NAMES]

    all_rows = []
    all_timings = []
    for task in anomaly_tasks.values():
        rows, timings = _run_task_under_configs(base_model, tokenizer, task, all_configs, split)
        all_rows += rows
        all_timings += timings
    for task in regression_tasks.values():
        rows, timings = _run_task_under_configs(base_model, tokenizer, task, regression_configs, split)
        all_rows += rows
        all_timings += timings

    print(render_markdown(all_rows))
    print()
    print(render_timing_markdown(all_timings))


if __name__ == "__main__":
    main()
