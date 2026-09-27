"""Sanity-layer extension of ADR 0025's deterministic shape-constraint
smoke test: same 8-task sample as ADR 0017/0023
(`sample_tiers.select_tier_tasks(..., "sanity")`), for direct
comparability with the diagnostic chain those ADRs built.

Usage: python -m src.evaluation.run_shape_constraint_sanity [training|evaluation]

Diagnostic only, does not decide a content-side lever, see
docs/decisions/0026-shape-constraint-sanity.md.
"""
import sys
from pathlib import Path

from src.evaluation.diagnostic_runner import render_timing_markdown
from src.evaluation.sample_tiers import select_tier_tasks
from src.evaluation.shape_constraint_diagnostics import (
    ShapeConstraintPairRow,
    diagnose_task_with_shape_constraint,
    render_markdown,
    save_config_rows,
)
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.model_loader import load_base_model
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "shape_constraint_sanity"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations" / "shape_constraint_sanity"


def _self_consistency_read(rows: list) -> str:
    """Per task, whether every train pair reaches exact_match (the same
    all-or-nothing bar neural_solver._passes_self_consistency applies),
    unconstrained vs. constrained. Reuses the rows already captured per
    pair instead of re-running generation, so this is a diagnostic read
    only, not a call into the real self-consistency gate."""
    by_task = {}
    for row in rows:
        if row.split == "train":
            by_task.setdefault(row.task_id, []).append(row)

    lines = [
        "| Task | Rule holds | Self-consistency (unconstrained) | Self-consistency (constrained) |",
        "|---|---|---|---|",
    ]
    for task_id, task_rows in by_task.items():
        rule_holds = task_rows[0].rule_holds
        unconstrained_pass = all(r.unconstrained_exact_match for r in task_rows)
        constrained_pass = all(r.constrained_exact_match for r in task_rows)
        lines.append(
            f"| {task_id} | {'yes' if rule_holds else 'no'} "
            f"| {'yes' if unconstrained_pass else 'no'} | {'yes' if constrained_pass else 'no'} |"
        )
    return "\n".join(lines)


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    config = NeuralSolverConfig()
    base_model, tokenizer = load_base_model(config)
    all_tasks = load_task_set(DATA_ROOT / split)
    tasks = select_tier_tasks(all_tasks, "sanity")

    all_rows: list = []
    all_timings = []
    for task_id, task in tasks.items():
        rows, timing = diagnose_task_with_shape_constraint(base_model, tokenizer, config, task, RAW_OUTPUT_ROOT / split)
        save_config_rows(f"shape_constraint_sanity_{task_id}", rows, OUTPUT_ROOT / split)
        all_rows += rows
        all_timings.append(timing)

    print(render_markdown(all_rows))
    print()
    print(_self_consistency_read(all_rows))
    print()
    print(render_timing_markdown(all_timings))


if __name__ == "__main__":
    main()
