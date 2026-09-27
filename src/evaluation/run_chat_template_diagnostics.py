"""Diagnostic-only re-run of ADR 0053's smoke test using the chat-template
prompt format (chat_prompt_builder.py) instead of prompt_builder.py's raw
completion format, to test whether Qwen3-Instruct's official chat interface
resolves the 3 new failure modes named in ADR 0053 (commentary tail,
sentence-level repetition, fabricated boxed block).

Usage: python -m src.evaluation.run_chat_template_diagnostics [training|evaluation] [limit|task_id1,task_id2,...]

Mirrors run_generation_diagnostics.py's structure and output format exactly
so the two can be compared side by side. Does not change any production
prompt-building, training, or generation code.
"""
import sys
from pathlib import Path
from typing import List

from src.evaluation.chat_template_generation_diagnostics import generate_with_counts_chat, train_on_task_chat
from src.evaluation.run_generation_diagnostics import PairDiagnosticRow, _render_markdown, _save_raw_completions, _save_task_rows
from src.evaluation.task_selector import parse_task_selector
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.lora_setup import attach_fresh_lora, detach_lora
from src.solvers.neural.model_loader import load_base_model
from src.utils.task_loader import Task, load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "chat_template_counts"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations_chat_template"


def _diagnose_pairs_chat(model, tokenizer, config, task_id: str, split: str, pairs, raw_output_dir: Path) -> List[PairDiagnosticRow]:
    rows = []
    for pair_index, pair in enumerate(pairs):
        diag = generate_with_counts_chat(model, tokenizer, pair.input, config)
        _save_raw_completions(task_id, split, pair_index, diag.raw_completions, raw_output_dir)
        exact_match = pair.output in diag.predictions
        rows.append(PairDiagnosticRow(
            task_id, split, pair_index, diag.attempts_tried, diag.num_parsed, diag.num_kept, exact_match,
        ))
    return rows


def diagnose_task_chat(base_model, tokenizer, config: NeuralSolverConfig, task: Task, raw_output_dir: Path) -> List[PairDiagnosticRow]:
    model = attach_fresh_lora(base_model, config)
    try:
        model = train_on_task_chat(model, tokenizer, task, config)
        rows = _diagnose_pairs_chat(model, tokenizer, config, task.task_id, "train", task.train, raw_output_dir)
        rows += _diagnose_pairs_chat(model, tokenizer, config, task.task_id, "test", task.test, raw_output_dir)
        return rows
    finally:
        detach_lora(model)


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
        rows = diagnose_task_chat(base_model, tokenizer, config, task, RAW_OUTPUT_ROOT / split)
        _save_task_rows(task_id, rows, OUTPUT_ROOT / split)
        all_rows += rows

    print(_render_markdown(all_rows))


if __name__ == "__main__":
    main()
