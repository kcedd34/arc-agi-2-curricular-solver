"""Shared per-task/per-pair diagnostic plumbing for smoke/sanity scripts
that compare NeuralSolverConfig variants (raw-text capture, generation
counts, and timing). Extracted from run_ablation_hyperparams.py so
run_augmentation_smoke.py does not duplicate it, per ADR 0021's addition
of direct timing capture (ADR 0019 had to reconstruct timing after the
fact from file timestamps, this measures it directly instead).
"""
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from src.evaluation.generation_diagnostics import generate_with_counts
from src.evaluation.pair_diagnostics import dimension_match
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.ttt_trainer import train_on_task
from src.utils.grid_types import Grid
from src.utils.task_loader import Task


@dataclass
class DiagnosticPairRow:
    config_name: str
    task_id: str
    split: str
    pair_index: int
    attempts_tried: int
    num_parsed: int
    num_kept: int
    num_copies_of_input: int
    exact_match: bool
    # None means there was no kept prediction to check at all (num_kept=0),
    # not that the shape failed to match. See ADR 0023.
    shape_matches_expected: Optional[bool] = None


@dataclass
class TimingRow:
    config_name: str
    task_id: str
    ttt_seconds: float
    total_seconds: float


def _count_copies_of_input(predictions: List[Grid], grid_input: Grid) -> int:
    return sum(1 for pred in predictions if pred == grid_input)


def _any_shape_match(predictions: List[Grid], expected: Grid) -> Optional[bool]:
    """None if there is nothing kept to check; otherwise whether at least one
    kept prediction has the expected output's grid shape, even if its
    content is wrong. Lets a diagnostic tell "close in structure" apart
    from "wrong every way" (see ADR 0023)."""
    if not predictions:
        return None
    return any(dimension_match(pred, expected) for pred in predictions)


def save_raw_completions(config_name: str, task_id: str, split: str, pair_index: int, raw_completions: List[str], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for attempt_index, text in enumerate(raw_completions):
        path = output_dir / f"{config_name}_{task_id}_{split}_{pair_index}_{attempt_index}.txt"
        path.write_text(text, encoding="utf-8")


def _diagnose_pairs(model, tokenizer, config, config_name, task_id, split, pairs, raw_output_dir) -> List[DiagnosticPairRow]:
    rows = []
    for pair_index, pair in enumerate(pairs):
        diag = generate_with_counts(model, tokenizer, pair.input, config)
        save_raw_completions(config_name, task_id, split, pair_index, diag.raw_completions, raw_output_dir)
        exact_match = pair.output in diag.predictions
        num_copies = _count_copies_of_input(diag.predictions, pair.input)
        shape_match = _any_shape_match(diag.predictions, pair.output)
        rows.append(DiagnosticPairRow(
            config_name, task_id, split, pair_index,
            diag.attempts_tried, diag.num_parsed, diag.num_kept, num_copies, exact_match,
            shape_match,
        ))
    return rows


def diagnose_task(base_model, tokenizer, config: NeuralSolverConfig, config_name: str, task: Task, raw_output_dir: Path) -> Tuple[List[DiagnosticPairRow], TimingRow]:
    # Lazy import: `unsloth` is only installed in the WSL GPU venv, not on
    # the host Python used to run the pure-logic test suite (see ADR 0023).
    # Deferring this keeps the rest of this module (render_markdown, the
    # counting helpers) host-testable without a GPU/unsloth dependency.
    from src.solvers.neural.lora_setup import attach_fresh_lora, detach_lora

    model = attach_fresh_lora(base_model, config)
    try:
        total_start = time.monotonic()
        model = train_on_task(model, tokenizer, task, config)
        ttt_seconds = time.monotonic() - total_start

        rows = _diagnose_pairs(model, tokenizer, config, config_name, task.task_id, "train", task.train, raw_output_dir)
        rows += _diagnose_pairs(model, tokenizer, config, config_name, task.task_id, "test", task.test, raw_output_dir)
        total_seconds = time.monotonic() - total_start

        timing = TimingRow(config_name, task.task_id, ttt_seconds, total_seconds)
        return rows, timing
    finally:
        detach_lora(model)


def save_config_rows(name: str, rows: List[DiagnosticPairRow], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{name}.json"
    path.write_text(json.dumps([asdict(r) for r in rows]), encoding="utf-8")


def _shape_match_cell(value: Optional[bool]) -> str:
    if value is None:
        return "n/a"
    return "yes" if value else "no"


def render_markdown(rows: List[DiagnosticPairRow]) -> str:
    header = "| Config | Task | Split | Pair | Attempts | Parsed | Kept | Copies of input | Exact match | Shape match |"
    separator = "|---|---|---|---|---|---|---|---|---|---|"
    body = [
        f"| {r.config_name} | {r.task_id} | {r.split} | {r.pair_index} | {r.attempts_tried} "
        f"| {r.num_parsed} | {r.num_kept} | {r.num_copies_of_input} | {'yes' if r.exact_match else 'no'} "
        f"| {_shape_match_cell(r.shape_matches_expected)} |"
        for r in rows
    ]
    return "\n".join([header, separator, *body])


def render_timing_markdown(timings: List[TimingRow]) -> str:
    header = "| Config | Task | TTT seconds | Total seconds |"
    separator = "|---|---|---|---|"
    body = [
        f"| {t.config_name} | {t.task_id} | {t.ttt_seconds:.2f} | {t.total_seconds:.2f} |"
        for t in timings
    ]
    return "\n".join([header, separator, *body])
