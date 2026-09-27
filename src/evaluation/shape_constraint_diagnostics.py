"""Per-task/per-pair diagnostics comparing unconstrained vs. shape-constrained
generation, for the ADR 0025 deterministic shape-constraint smoke test.

Runs generate_with_counts only ONCE per pair: shape_rule's
output_shape_equals_input_shape(task) decides whether force_grid_shape is
applied on top of those same raw predictions, so both the "current
behavior" (unconstrained) and the "constrained" reading come from a single
GPU generation pass, not two. See docs/decisions/0025-deterministic-shape-constraint.md.
"""
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from src.evaluation.diagnostic_runner import TimingRow, save_config_rows, save_raw_completions
from src.evaluation.generation_diagnostics import generate_with_counts
from src.evaluation.pair_diagnostics import dimension_match, per_cell_accuracy
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.shape_constraint import force_grid_shape
from src.solvers.neural.shape_rule import output_shape_equals_input_shape
from src.utils.grid_types import Grid
from src.utils.task_loader import Task

CONFIG_NAME = "shape_constraint"


@dataclass
class ShapeConstraintPairRow:
    task_id: str
    rule_holds: bool
    split: str
    pair_index: int
    attempts_tried: int
    num_kept: int
    unconstrained_shape_match: Optional[bool]
    unconstrained_exact_match: bool
    constrained_shape_match: Optional[bool]
    constrained_exact_match: bool
    # Best per-cell accuracy among constrained predictions that share the
    # expected shape, for reading content proximity ("close" vs. "far")
    # once shape is no longer a confound. None if no constrained
    # prediction shares the expected shape (nothing comparable cell-by-cell).
    constrained_best_cell_accuracy: Optional[float]


def _shape(grid: Grid) -> Tuple[int, int]:
    return (len(grid), len(grid[0]) if grid else 0)


def _any_shape_match(predictions: List[Grid], expected: Grid) -> Optional[bool]:
    """None if there is nothing kept to check, mirroring diagnostic_runner's
    convention (ADR 0023)."""
    if not predictions:
        return None
    return any(dimension_match(pred, expected) for pred in predictions)


def _apply_constraint(predictions: List[Grid], target_shape: Tuple[int, int]) -> List[Grid]:
    target_rows, target_cols = target_shape
    return [force_grid_shape(pred, target_rows, target_cols) for pred in predictions]


def _best_cell_accuracy(predictions: List[Grid], expected: Grid) -> Optional[float]:
    accuracies = [a for a in (per_cell_accuracy(p, expected) for p in predictions) if a is not None]
    return max(accuracies) if accuracies else None


def _diagnose_pair_with_constraint(model, tokenizer, config, task_id, rule_holds, split, pair_index, pair, raw_output_dir) -> ShapeConstraintPairRow:
    diag = generate_with_counts(model, tokenizer, pair.input, config)
    save_raw_completions(CONFIG_NAME, task_id, split, pair_index, diag.raw_completions, raw_output_dir)

    unconstrained_shape_match = _any_shape_match(diag.predictions, pair.output)
    unconstrained_exact_match = pair.output in diag.predictions

    if rule_holds:
        constrained_predictions = _apply_constraint(diag.predictions, _shape(pair.input))
    else:
        constrained_predictions = diag.predictions

    constrained_shape_match = _any_shape_match(constrained_predictions, pair.output)
    constrained_exact_match = pair.output in constrained_predictions
    constrained_best_cell_accuracy = _best_cell_accuracy(constrained_predictions, pair.output)

    return ShapeConstraintPairRow(
        task_id, rule_holds, split, pair_index,
        diag.attempts_tried, diag.num_kept,
        unconstrained_shape_match, unconstrained_exact_match,
        constrained_shape_match, constrained_exact_match,
        constrained_best_cell_accuracy,
    )


def diagnose_task_with_shape_constraint(base_model, tokenizer, config: NeuralSolverConfig, task: Task, raw_output_dir: Path) -> Tuple[List[ShapeConstraintPairRow], TimingRow]:
    # Lazy import: unsloth only exists in the WSL GPU venv, not on the host
    # Python used for the pure-logic test suite (same boundary as ADR 0023).
    from src.solvers.neural.lora_setup import attach_fresh_lora, detach_lora
    from src.solvers.neural.ttt_trainer import train_on_task

    rule_holds = output_shape_equals_input_shape(task)
    model = attach_fresh_lora(base_model, config)
    try:
        total_start = time.monotonic()
        model = train_on_task(model, tokenizer, task, config)
        ttt_seconds = time.monotonic() - total_start

        rows = [
            _diagnose_pair_with_constraint(model, tokenizer, config, task.task_id, rule_holds, "train", i, pair, raw_output_dir)
            for i, pair in enumerate(task.train)
        ]
        rows += [
            _diagnose_pair_with_constraint(model, tokenizer, config, task.task_id, rule_holds, "test", i, pair, raw_output_dir)
            for i, pair in enumerate(task.test)
        ]
        total_seconds = time.monotonic() - total_start

        timing = TimingRow(CONFIG_NAME, task.task_id, ttt_seconds, total_seconds)
        return rows, timing
    finally:
        detach_lora(model)


def _cell(value: Optional[bool]) -> str:
    if value is None:
        return "n/a"
    return "yes" if value else "no"


def _accuracy_cell(value: Optional[float]) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def render_markdown(rows: List[ShapeConstraintPairRow]) -> str:
    header = ("| Task | Rule holds | Split | Pair | Attempts | Kept "
               "| Unconstr. shape | Unconstr. exact | Constr. shape | Constr. exact | Constr. cell acc |")
    separator = "|---|---|---|---|---|---|---|---|---|---|---|"
    body = [
        f"| {r.task_id} | {'yes' if r.rule_holds else 'no'} | {r.split} | {r.pair_index} | {r.attempts_tried} "
        f"| {r.num_kept} | {_cell(r.unconstrained_shape_match)} | {'yes' if r.unconstrained_exact_match else 'no'} "
        f"| {_cell(r.constrained_shape_match)} | {'yes' if r.constrained_exact_match else 'no'} "
        f"| {_accuracy_cell(r.constrained_best_cell_accuracy)} |"
        for r in rows
    ]
    return "\n".join([header, separator, *body])


__all__ = [
    "ShapeConstraintPairRow",
    "diagnose_task_with_shape_constraint",
    "render_markdown",
    "save_config_rows",
]
