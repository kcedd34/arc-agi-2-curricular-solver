"""Per-task/per-pair diagnostics for ADR 0031's conditional escalation
policy: same shape-constrained reading and failure-mode counts as
mitigation_diagnostics.py (ADR 0029/0030), but generation goes through
conditional_generation_diagnostics.generate_with_conditional_counts instead
of the fixed-config generate_with_counts, and each row also records whether
its pair triggered escalation.
"""
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from src.evaluation.conditional_generation_diagnostics import generate_with_conditional_counts
from src.evaluation.diagnostic_runner import TimingRow, save_config_rows, save_raw_completions
from src.evaluation.failure_mode_diagnostics import has_degenerate_repetition, has_hallucinated_second_example
from src.evaluation.pair_diagnostics import per_cell_accuracy
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.generation import _generate_completion
from src.solvers.neural.prompt_builder import build_inference_prompt
from src.solvers.neural.shape_constraint import force_grid_shape
from src.solvers.neural.shape_rule import output_shape_equals_input_shape
from src.utils.grid_types import Grid
from src.utils.task_loader import Task


@dataclass
class ConditionalMitigationPairRow:
    config_name: str
    task_id: str
    split: str
    pair_index: int
    attempts_tried: int
    num_kept: int
    num_hallucinated: int
    num_repetitive: int
    escalated: bool
    constrained_exact_match: bool
    constrained_best_cell_accuracy: Optional[float]


def _shape(grid: Grid) -> Tuple[int, int]:
    return (len(grid), len(grid[0]) if grid else 0)


def _apply_constraint(predictions: List[Grid], target_shape: Tuple[int, int]) -> List[Grid]:
    target_rows, target_cols = target_shape
    return [force_grid_shape(pred, target_rows, target_cols) for pred in predictions]


def _best_cell_accuracy(predictions: List[Grid], expected: Grid) -> Optional[float]:
    accuracies = [a for a in (per_cell_accuracy(p, expected) for p in predictions) if a is not None]
    return max(accuracies) if accuracies else None


def _diagnose_pair(model, tokenizer, config, config_name, task_id, rule_holds, split, pair_index, pair, raw_output_dir, enable_conditional_escalation) -> ConditionalMitigationPairRow:
    prompt = build_inference_prompt(pair.input)

    def generate_completion(active_config, seed):
        return _generate_completion(model, tokenizer, prompt, active_config, seed)

    diag = generate_with_conditional_counts(generate_completion, config, enable_conditional_escalation)
    save_raw_completions(config_name, task_id, split, pair_index, diag.raw_completions, raw_output_dir)

    num_hallucinated = sum(1 for c in diag.raw_completions if has_hallucinated_second_example(c))
    num_repetitive = sum(1 for c in diag.raw_completions if has_degenerate_repetition(c))

    if rule_holds:
        constrained_predictions = _apply_constraint(diag.predictions, _shape(pair.input))
    else:
        constrained_predictions = diag.predictions

    constrained_exact_match = pair.output in constrained_predictions
    constrained_best_cell_accuracy = _best_cell_accuracy(constrained_predictions, pair.output)

    return ConditionalMitigationPairRow(
        config_name, task_id, split, pair_index,
        diag.attempts_tried, diag.num_kept, num_hallucinated, num_repetitive, diag.escalated,
        constrained_exact_match, constrained_best_cell_accuracy,
    )


def diagnose_task_with_conditional_mitigation(base_model, tokenizer, config: NeuralSolverConfig, config_name: str, task: Task, raw_output_dir: Path, enable_conditional_escalation: bool = True) -> Tuple[List[ConditionalMitigationPairRow], TimingRow]:
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
            _diagnose_pair(model, tokenizer, config, config_name, task.task_id, rule_holds, "train", i, pair, raw_output_dir, enable_conditional_escalation)
            for i, pair in enumerate(task.train)
        ]
        rows += [
            _diagnose_pair(model, tokenizer, config, config_name, task.task_id, rule_holds, "test", i, pair, raw_output_dir, enable_conditional_escalation)
            for i, pair in enumerate(task.test)
        ]
        total_seconds = time.monotonic() - total_start

        timing = TimingRow(config_name, task.task_id, ttt_seconds, total_seconds)
        return rows, timing
    finally:
        detach_lora(model)


def _accuracy_cell(value: Optional[float]) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def render_markdown(rows: List[ConditionalMitigationPairRow]) -> str:
    header = ("| Config | Task | Split | Pair | Attempts | Kept "
              "| Hallucinated | Repetitive | Escalated | Exact match | Cell acc |")
    separator = "|---|---|---|---|---|---|---|---|---|---|---|"
    body = [
        f"| {r.config_name} | {r.task_id} | {r.split} | {r.pair_index} | {r.attempts_tried} "
        f"| {r.num_kept} | {r.num_hallucinated} | {r.num_repetitive} | {'yes' if r.escalated else 'no'} "
        f"| {'yes' if r.constrained_exact_match else 'no'} | {_accuracy_cell(r.constrained_best_cell_accuracy)} |"
        for r in rows
    ]
    return "\n".join([header, separator, *body])


__all__ = [
    "ConditionalMitigationPairRow",
    "diagnose_task_with_conditional_mitigation",
    "render_markdown",
    "save_config_rows",
]
