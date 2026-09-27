"""Sanity-layer comparison of color augmentation on top of the existing
geometric augmentation, gated by the sanity-tier shape constraint (ADR
0025/0026) so exact_match/per-cell-accuracy stay readable without shape as
a confound. Same 8-task sample as ADR 0017/0023/0024/0026
(`sample_tiers.select_tier_tasks(..., "sanity")`).

Usage: python -m src.evaluation.run_color_augmentation_sanity [training|evaluation]

Diagnostic only, does not decide whether color augmentation becomes a
production default, see docs/decisions/0027-color-augmentation-sanity.md.
"""
import sys
from pathlib import Path

from src.evaluation.color_augmentation_configs import build_color_augmentation_configs
from src.evaluation.color_augmentation_diagnostics import render_comparison_markdown, run_config_on_tasks
from src.evaluation.diagnostic_runner import render_timing_markdown
from src.evaluation.sample_tiers import select_tier_tasks
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.model_loader import load_base_model
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "color_augmentation_sanity"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations" / "color_augmentation_sanity"


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    base_model, tokenizer = load_base_model(NeuralSolverConfig())
    all_tasks = load_task_set(DATA_ROOT / split)
    tasks = select_tier_tasks(all_tasks, "sanity")

    rows_by_config = {}
    all_timings = []
    for config_name, config in build_color_augmentation_configs():
        rows, timings = run_config_on_tasks(
            base_model, tokenizer, config_name, config, tasks, RAW_OUTPUT_ROOT, OUTPUT_ROOT, split
        )
        rows_by_config[config_name] = rows
        all_timings += timings

    print(render_comparison_markdown(rows_by_config))
    print()
    print(render_timing_markdown(all_timings))


if __name__ == "__main__":
    main()
