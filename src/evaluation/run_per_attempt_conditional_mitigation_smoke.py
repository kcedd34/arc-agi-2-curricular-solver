"""Sanity-tier test of the per-attempt conditional escalation policy: same
as ADR 0031's conditional policy (run_conditional_mitigation_smoke.py), but
every attempt's own completion is checked for ADR 0028's degenerate
pattern, not only the first, and escalation to ADR 0030's ngram_only config
triggers as soon as any attempt so far shows it
(per_attempt_conditional_generation_diagnostics).

Runs once on the same 8-task sanity sample used throughout ADR 0026-0031,
with escalation enabled. baseline and ngram_only are not re-run, both
already fully persisted/logged by ADR 0029/0030 on this same sample;
ADR 0031's first-attempt-only conditional run is also not re-run, already
persisted under outputs/diagnostics/conditional_mitigation_smoke/.

Usage: python -m src.evaluation.run_per_attempt_conditional_mitigation_smoke [training|evaluation]

Diagnostic only, does not decide production-default status, see
docs/decisions/0032-per-attempt-conditional-ngram-mitigation.md.
"""
import sys
from pathlib import Path

from src.evaluation.diagnostic_runner import render_timing_markdown
from src.evaluation.per_attempt_conditional_mitigation_pair_diagnostics import (
    diagnose_task_with_per_attempt_conditional_mitigation,
    render_markdown,
    save_config_rows,
)
from src.evaluation.sample_tiers import select_tier_tasks
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.model_loader import load_base_model
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "per_attempt_conditional_mitigation_smoke"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations" / "per_attempt_conditional_mitigation_smoke"
CONFIG_NAME = "conditional_per_attempt"


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    base_model, tokenizer = load_base_model(NeuralSolverConfig())
    all_tasks = load_task_set(DATA_ROOT / split)
    sanity_tasks = select_tier_tasks(all_tasks, "sanity")
    baseline_config = NeuralSolverConfig()

    all_rows = []
    all_timings = []
    for task in sanity_tasks.values():
        rows, timing = diagnose_task_with_per_attempt_conditional_mitigation(
            base_model, tokenizer, baseline_config, CONFIG_NAME, task, RAW_OUTPUT_ROOT / split,
            enable_conditional_escalation=True,
        )
        save_config_rows(f"per_attempt_conditional_mitigation_smoke_{CONFIG_NAME}_{task.task_id}", rows, OUTPUT_ROOT / split)
        all_rows += rows
        all_timings.append(timing)

    print(render_markdown(all_rows))
    print()
    print(render_timing_markdown(all_timings))


if __name__ == "__main__":
    main()
