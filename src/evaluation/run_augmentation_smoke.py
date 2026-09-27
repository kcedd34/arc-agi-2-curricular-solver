"""Geometric augmentation smoke test (ADR 0021): a genuine no-augmentation
control vs. the full 8-transform D4 augmentation, on the same 2 tasks
ADR 0018/0019 used. Checks whether the "copies the input" pattern
disappears on the held-out TEST pair (not just a train pair), and measures
the TTT time cost of up to 8x more training examples per task.

Usage: python -m src.evaluation.run_augmentation_smoke [training|evaluation] [task_id1,task_id2,...]
Omit the task selector to use the same two ADR 0018/0019 tasks by default.

Diagnostic only, does not change solver defaults or pick a final variant
count, see docs/decisions/0021-augmentation-geometric-smoke-test.md.
"""
import sys
from pathlib import Path

from src.evaluation.augmentation_configs import build_augmentation_configs
from src.evaluation.diagnostic_runner import diagnose_task, render_markdown, render_timing_markdown, save_config_rows
from src.evaluation.task_selector import parse_task_selector
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.model_loader import load_base_model
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "augmentation"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations" / "augmentation"
DEFAULT_TASK_IDS = ["136b0064", "135a2760"]


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    _, selected_ids = parse_task_selector(sys.argv[2]) if len(sys.argv) > 2 else (None, None)
    task_ids = selected_ids or DEFAULT_TASK_IDS

    base_config = NeuralSolverConfig()
    base_model, tokenizer = load_base_model(base_config)
    all_tasks = load_task_set(DATA_ROOT / split)
    tasks = {task_id: all_tasks[task_id] for task_id in task_ids if task_id in all_tasks}

    all_rows = []
    all_timings = []
    for config_name, config in build_augmentation_configs():
        for task_id, task in tasks.items():
            rows, timing = diagnose_task(base_model, tokenizer, config, config_name, task, RAW_OUTPUT_ROOT / split)
            save_config_rows(f"{config_name}_{task_id}", rows, OUTPUT_ROOT / split)
            all_rows += rows
            all_timings.append(timing)

    print(render_markdown(all_rows))
    print()
    print(render_timing_markdown(all_timings))


if __name__ == "__main__":
    main()
