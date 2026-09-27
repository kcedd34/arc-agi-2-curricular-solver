"""Diagnostic-only re-run of TTT + generation on a task sample, reporting raw
sampling counts instead of final predictions, and persisting each sampling
attempt's raw decoded text (before parsing) under outputs/raw_generations/.
Investigates whether the neural solver's empty-candidate outcome (ADR 0008)
comes from the self-consistency filter rejecting otherwise-valid samples,
from generation/parsing never producing a valid grid in the first place
(ADR 0009), or from truncated/malformed raw text (ADR 0010).

Usage: python -m src.evaluation.run_generation_diagnostics [training|evaluation] [limit|task_id1,task_id2,...]

Does not change solver behavior and does not decide or apply any fix; see
docs/decisions/0009-empty-candidate-diagnosis.md and
docs/decisions/0010-raw-generation-inspection.md.
"""
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

from src.evaluation.generation_diagnostics import generate_with_counts
from src.evaluation.task_selector import parse_task_selector
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.lora_setup import attach_fresh_lora, detach_lora
from src.solvers.neural.model_loader import load_base_model
from src.solvers.neural.ttt_trainer import train_on_task
from src.utils.task_loader import Task, load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "generation_counts"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations"


@dataclass
class PairDiagnosticRow:
    task_id: str
    split: str
    pair_index: int
    attempts_tried: int
    num_parsed: int
    num_parsed_but_degenerate: int
    num_kept: int
    exact_match: bool


def _save_raw_completions(task_id: str, split: str, pair_index: int, raw_completions: List[str], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for attempt_index, text in enumerate(raw_completions):
        path = output_dir / f"{task_id}_{split}_{pair_index}_{attempt_index}.txt"
        path.write_text(text, encoding="utf-8")


def _diagnose_pairs(model, tokenizer, config, task_id: str, split: str, pairs, raw_output_dir: Path) -> List[PairDiagnosticRow]:
    rows = []
    for pair_index, pair in enumerate(pairs):
        diag = generate_with_counts(model, tokenizer, pair.input, config)
        _save_raw_completions(task_id, split, pair_index, diag.raw_completions, raw_output_dir)
        exact_match = pair.output in diag.predictions
        rows.append(PairDiagnosticRow(
            task_id, split, pair_index, diag.attempts_tried, diag.num_parsed,
            diag.num_parsed_but_degenerate, diag.num_kept, exact_match,
        ))
    return rows


def diagnose_task(base_model, tokenizer, config: NeuralSolverConfig, task: Task, raw_output_dir: Path) -> List[PairDiagnosticRow]:
    model = attach_fresh_lora(base_model, config)
    try:
        model = train_on_task(model, tokenizer, task, config)
        rows = _diagnose_pairs(model, tokenizer, config, task.task_id, "train", task.train, raw_output_dir)
        rows += _diagnose_pairs(model, tokenizer, config, task.task_id, "test", task.test, raw_output_dir)
        return rows
    finally:
        detach_lora(model)


def _save_task_rows(task_id: str, rows: List[PairDiagnosticRow], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{task_id}.json"
    path.write_text(json.dumps([asdict(r) for r in rows]), encoding="utf-8")


def _render_markdown(rows: List[PairDiagnosticRow]) -> str:
    header = "| Task | Split | Pair | Attempts tried | Parsed | Parsed-but-degenerate | Kept | Exact match |"
    separator = "|---|---|---|---|---|---|---|---|"
    body = [
        f"| {r.task_id} | {r.split} | {r.pair_index} | {r.attempts_tried} | {r.num_parsed} "
        f"| {r.num_parsed_but_degenerate} | {r.num_kept} | {'yes' if r.exact_match else 'no'} |"
        for r in rows
    ]
    return "\n".join([header, separator, *body])


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    limit, task_ids = parse_task_selector(sys.argv[2]) if len(sys.argv) > 2 else (None, None)
    config = NeuralSolverConfig()
    base_model, tokenizer = load_base_model(config)
    tasks = load_task_set(DATA_ROOT / split)
    if task_ids is not None:
        tasks = {task_id: tasks[task_id] for task_id in task_ids if task_id in tasks}
    elif limit is not None:
        tasks = dict(list(tasks.items())[:limit])

    all_rows: List[PairDiagnosticRow] = []
    for task_id, task in tasks.items():
        rows = diagnose_task(base_model, tokenizer, config, task, RAW_OUTPUT_ROOT / split)
        _save_task_rows(task_id, rows, OUTPUT_ROOT / split)
        all_rows += rows

    print(_render_markdown(all_rows))


if __name__ == "__main__":
    main()
