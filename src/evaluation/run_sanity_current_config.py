"""Sanity-layer diagnostic run (8 tasks) of the current, mature
NeuralSolverConfig: full 8-element D4 geometric augmentation (ADR 0021)
plus the ADR 0010 EOS fix, both already the config defaults. Uses the
same deterministic task selection as ADR 0017's sanity run
(`sample_tiers.select_tier_tasks`, "sanity" tier: first 8 tasks sorted
by id), for a direct, same-sample comparison.

Captures, per test pair (train pairs too, for context): exact_match,
num_copies_of_input, and whether any kept prediction at least matches
the expected output's grid shape, to tell "close in structure" apart
from "wrong every way".

Usage: python -m src.evaluation.run_sanity_current_config [training|evaluation]

Diagnostic only, does not decide or implement a lever, see
docs/decisions/0023-sanity-current-config-post-augmentation.md.
"""
import sys
from pathlib import Path

from src.evaluation.diagnostic_runner import diagnose_task, render_markdown, render_timing_markdown, save_config_rows
from src.evaluation.sample_tiers import select_tier_tasks
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.model_loader import load_base_model
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "sanity_current_config"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations" / "sanity_current_config"
CONFIG_NAME = "current_config"


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    config = NeuralSolverConfig()
    base_model, tokenizer = load_base_model(config)
    all_tasks = load_task_set(DATA_ROOT / split)
    tasks = select_tier_tasks(all_tasks, "sanity")

    all_rows = []
    all_timings = []
    for task_id, task in tasks.items():
        rows, timing = diagnose_task(base_model, tokenizer, config, CONFIG_NAME, task, RAW_OUTPUT_ROOT / split)
        save_config_rows(f"{CONFIG_NAME}_{task_id}", rows, OUTPUT_ROOT / split)
        all_rows += rows
        all_timings.append(timing)

    print(render_markdown(all_rows))
    print()
    print(render_timing_markdown(all_timings))


if __name__ == "__main__":
    main()
