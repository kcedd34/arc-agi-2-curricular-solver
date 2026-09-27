"""Deterministic shape-constraint smoke test (ADR 0025): compares
unconstrained vs. shape-constrained generation on tasks ADR 0024 already
diagnosed as having the "output shape equals input shape" rule confirmed
across all train pairs, and that showed row-count errors on held-out test
pairs.

Only ONE generation pass per pair is run; both readings come from
post-processing the same raw predictions (see shape_constraint_diagnostics.py).

Usage: python -m src.evaluation.run_shape_constraint_smoke [training|evaluation] [task_id1,task_id2,...]
Omit the task selector to use the default two-task smoke sample.

Diagnostic only, does not change solver defaults, see
docs/decisions/0025-deterministic-shape-constraint.md.
"""
import sys
from pathlib import Path

from src.evaluation.shape_constraint_diagnostics import (
    diagnose_task_with_shape_constraint,
    render_markdown,
    save_config_rows,
)
from src.evaluation.diagnostic_runner import render_timing_markdown
from src.evaluation.task_selector import parse_task_selector
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.model_loader import load_base_model
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "shape_constraint"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations" / "shape_constraint"
# Both showed row-count-only undershoot in ADR 0024 (no column-width issue),
# and both have output_shape_equals_input_shape confirmed on every train pair.
DEFAULT_TASK_IDS = ["135a2760", "1818057f"]


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    _, selected_ids = parse_task_selector(sys.argv[2]) if len(sys.argv) > 2 else (None, None)
    task_ids = selected_ids or DEFAULT_TASK_IDS

    config = NeuralSolverConfig()
    base_model, tokenizer = load_base_model(config)
    all_tasks = load_task_set(DATA_ROOT / split)
    tasks = {task_id: all_tasks[task_id] for task_id in task_ids if task_id in all_tasks}

    all_rows = []
    all_timings = []
    for task_id, task in tasks.items():
        rows, timing = diagnose_task_with_shape_constraint(base_model, tokenizer, config, task, RAW_OUTPUT_ROOT / split)
        save_config_rows(f"shape_constraint_{task_id}", rows, OUTPUT_ROOT / split)
        all_rows += rows
        all_timings.append(timing)

    print(render_markdown(all_rows))
    print()
    print(render_timing_markdown(all_timings))


if __name__ == "__main__":
    main()
