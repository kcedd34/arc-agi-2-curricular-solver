"""Sanity-tier test of ADR 0031's conditional escalation policy: runs every
pair's first attempt with the plain baseline config (no_repeat_ngram_size=0),
and escalates only that pair's remaining attempts to ADR 0030's ngram_only
config if the first attempt shows a degenerate pattern
(src.solvers.neural.conditional_mitigation, ADR 0028's two failure modes).

Runs once on the same 8-task sanity sample used throughout ADR 0026-0030,
with escalation enabled. baseline (escalation impossible, since no attempt
ever triggers it) and ngram_only (escalation applied to every pair
unconditionally) are not re-run here, both already fully persisted/logged
by ADR 0029/0030 on this same sample and reused unchanged for comparison.

Usage: python -m src.evaluation.run_conditional_mitigation_smoke [training|evaluation]

Diagnostic only, does not decide production-default status, see
docs/decisions/0031-conditional-ngram-mitigation.md.
"""
import sys
from pathlib import Path

from src.evaluation.conditional_mitigation_pair_diagnostics import (
    diagnose_task_with_conditional_mitigation,
    render_markdown,
    save_config_rows,
)
from src.evaluation.diagnostic_runner import render_timing_markdown
from src.evaluation.sample_tiers import select_tier_tasks
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.model_loader import load_base_model
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "conditional_mitigation_smoke"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations" / "conditional_mitigation_smoke"
CONFIG_NAME = "conditional"


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    base_model, tokenizer = load_base_model(NeuralSolverConfig())
    all_tasks = load_task_set(DATA_ROOT / split)
    sanity_tasks = select_tier_tasks(all_tasks, "sanity")
    baseline_config = NeuralSolverConfig()

    all_rows = []
    all_timings = []
    for task in sanity_tasks.values():
        rows, timing = diagnose_task_with_conditional_mitigation(
            base_model, tokenizer, baseline_config, CONFIG_NAME, task, RAW_OUTPUT_ROOT / split,
            enable_conditional_escalation=True,
        )
        save_config_rows(f"conditional_mitigation_smoke_{CONFIG_NAME}_{task.task_id}", rows, OUTPUT_ROOT / split)
        all_rows += rows
        all_timings.append(timing)

    print(render_markdown(all_rows))
    print()
    print(render_timing_markdown(all_timings))


if __name__ == "__main__":
    main()
