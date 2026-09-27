"""Sanity-layer diagnostics comparing geometric-only vs. geometric-plus-color
augmentation, with the sanity-tier shape constraint (ADR 0025/0026) already
applied to every generated prediction, so exact_match/per-cell-accuracy
stay readable without shape as a confound.

Unlike ADR 0025/0026 (one generation pass, two readings from it), the
config itself changes what TTT trains on here, so this runs
shape_constraint_diagnostics' diagnose_task_with_shape_constraint once per
(task, config) pair: two full TTT+generation passes per task, one per
color-augmentation setting. See docs/decisions/0027-color-augmentation-sanity.md.
"""
from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.evaluation.diagnostic_runner import TimingRow
from src.evaluation.shape_constraint_diagnostics import (
    ShapeConstraintPairRow,
    diagnose_task_with_shape_constraint,
    save_config_rows,
)
from src.solvers.neural.config import NeuralSolverConfig
from src.utils.task_loader import Task

CONFIG_NAMES = ("geometric_only", "geometric_plus_color")


def _bool_cell(value: Optional[bool]) -> str:
    if value is None:
        return "n/a"
    return "yes" if value else "no"


def _accuracy_cell(value: Optional[float]) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def run_config_on_tasks(
    base_model, tokenizer, config_name: str, config: NeuralSolverConfig,
    tasks: Dict[str, Task], raw_output_root: Path, output_root: Path, split: str,
) -> Tuple[List[ShapeConstraintPairRow], List[TimingRow]]:
    rows: List[ShapeConstraintPairRow] = []
    timings: List[TimingRow] = []
    for task_id, task in tasks.items():
        raw_dir = raw_output_root / split / config_name
        task_rows, timing = diagnose_task_with_shape_constraint(base_model, tokenizer, config, task, raw_dir)
        save_config_rows(f"color_aug_{config_name}_{task_id}", task_rows, output_root / split)
        rows += task_rows
        timings.append(replace(timing, config_name=config_name))
    return rows, timings


def render_comparison_markdown(rows_by_config: Dict[str, List[ShapeConstraintPairRow]]) -> str:
    header = ("| Config | Task | Rule holds | Split | Pair | Constr. shape "
               "| Constr. exact | Constr. cell acc |")
    separator = "|---|---|---|---|---|---|---|---|"
    body = [
        f"| {config_name} | {r.task_id} | {'yes' if r.rule_holds else 'no'} | {r.split} | {r.pair_index} "
        f"| {_bool_cell(r.constrained_shape_match)} | {'yes' if r.constrained_exact_match else 'no'} "
        f"| {_accuracy_cell(r.constrained_best_cell_accuracy)} |"
        for config_name, rows in rows_by_config.items()
        for r in rows
    ]
    return "\n".join([header, separator, *body])


__all__ = [
    "CONFIG_NAMES",
    "run_config_on_tasks",
    "render_comparison_markdown",
]
