"""Smoke-tier follow-up to ADR 0029: splits its combined `repetition_only`
axis (repetition_penalty=1.3 AND no_repeat_ngram_size=3 together) into two
isolated configs, penalty_only and ngram_only
(src/evaluation/decoding_mitigation_configs.py), to find which parameter
drives the held-out-accuracy regression ADR 0029 found on the 6 tasks that
never showed either failure mode.

Runs both new configs on the full 8-task sanity sample (the 2 tasks
affected by the failure modes plus the 6 regression-check tasks), so all
four of ADR 0029's comparison criteria can be read for each new config
directly against its four already-run configs (baseline, repetition_only,
stop_heuristic_only, both), reusing that already-persisted/logged data
instead of re-running it.

Usage: python -m src.evaluation.run_repetition_split_smoke [training|evaluation]

Diagnostic only, does not decide production-default status, see
docs/decisions/0030-splitting-repetition-mitigation-parameters.md.
"""
import sys
from pathlib import Path

from src.evaluation.decoding_mitigation_configs import build_repetition_axis_split_configs
from src.evaluation.diagnostic_runner import render_timing_markdown
from src.evaluation.mitigation_diagnostics import diagnose_task_with_mitigations, render_markdown, save_config_rows
from src.evaluation.sample_tiers import select_tier_tasks
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.model_loader import load_base_model
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "repetition_split_smoke"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations" / "repetition_split_smoke"


def _run_task_under_configs(base_model, tokenizer, task, configs, split):
    all_rows = []
    all_timings = []
    for config_name, config in configs:
        rows, timing = diagnose_task_with_mitigations(
            base_model, tokenizer, config, config_name, task, RAW_OUTPUT_ROOT / split
        )
        save_config_rows(f"repetition_split_smoke_{config_name}_{task.task_id}", rows, OUTPUT_ROOT / split)
        all_rows += rows
        all_timings.append(timing)
    return all_rows, all_timings


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    base_model, tokenizer = load_base_model(NeuralSolverConfig())
    all_tasks = load_task_set(DATA_ROOT / split)
    sanity_tasks = select_tier_tasks(all_tasks, "sanity")
    split_configs = build_repetition_axis_split_configs()

    all_rows = []
    all_timings = []
    for task in sanity_tasks.values():
        rows, timings = _run_task_under_configs(base_model, tokenizer, task, split_configs, split)
        all_rows += rows
        all_timings += timings

    print(render_markdown(all_rows))
    print()
    print(render_timing_markdown(all_timings))


if __name__ == "__main__":
    main()
