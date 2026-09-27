"""Cross-task pretraining pilot (ADR 0022/0035), see
docs/decisions/0036-piloto-pretreino-cross-task.md.

Two phases against the same base model process:
1. Cross-task pretraining: one shared LoRA adapter trained across
   `pretraining_size` tasks from the training split, disjoint from the
   reserved sanity/validation evaluation tasks by construction
   (pretraining_split.py), with checkpointing enabled so the phase can be
   interrupted and resumed (checkpoint_utils.find_resumable_checkpoint).
2. Per-task TTT warm-started from that pretrained adapter
   (lora_setup.attach_pretrained_lora), run on the reserved evaluation
   tasks (the union of the sanity and validation tiers,
   reserved_evaluation_tasks.py) through the exact same diagnostic code
   path ADR 0034's baseline numbers came from, just with adapter_dir set.

Usage: python -m src.evaluation.run_cross_task_pretraining_pilot [pretraining_size] [eval_size_override]
"""
import sys
import time
from dataclasses import replace
from pathlib import Path

from src.evaluation.color_augmentation_configs import build_color_augmentation_configs
from src.evaluation.diagnostic_runner import render_timing_markdown
from src.evaluation.per_attempt_conditional_mitigation_pair_diagnostics import (
    diagnose_task_with_per_attempt_conditional_mitigation,
    render_markdown,
    save_config_rows,
)
from src.evaluation.pretraining_split import save_split_manifest, select_pretraining_tasks_excluding_reserved
from src.evaluation.reserved_evaluation_tasks import reserved_evaluation_task_ids
from src.evaluation.sample_tiers import select_tier_tasks
from src.evaluation.validation_run_summary import (
    exact_match_rate,
    far_outlier_task_ids,
    per_cell_accuracy_distribution,
)
from src.solvers.neural.checkpoint_utils import find_resumable_checkpoint
from src.solvers.neural.cross_task_pretraining import pretrain_shared_adapter
from src.solvers.neural.lora_setup import attach_fresh_lora, detach_lora
from src.solvers.neural.model_loader import load_base_model
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "cross_task_pretraining_pilot"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations" / "cross_task_pretraining_pilot"
ADAPTER_DIR = str(PROJECT_ROOT / "outputs" / "adapters" / "cross_task_pretrained")
SPLIT_MANIFEST_PATH = OUTPUT_ROOT / "pretraining_pilot_split.json"
PRETRAINING_CHECKPOINT_DIR = str(PROJECT_ROOT / "outputs" / "ttt_tmp" / "cross_task_pretraining_pilot")
CONFIG_NAME = "cross_task_pretrained_warm_start"
DEFAULT_PRETRAINING_TASK_COUNT = 150


def _consolidated_config():
    configs = dict(build_color_augmentation_configs())
    return configs["geometric_plus_color"]


def _select_pretraining_tasks(pretraining_size):
    training_tasks = load_task_set(DATA_ROOT / "training")
    reserved_ids = reserved_evaluation_task_ids()
    selected = select_pretraining_tasks_excluding_reserved(training_tasks, pretraining_size, reserved_ids)
    save_split_manifest(list(selected), SPLIT_MANIFEST_PATH)
    return selected


def _select_eval_tasks(eval_size_override):
    evaluation_tasks_pool = load_task_set(DATA_ROOT / "evaluation")
    reserved_ids = sorted(reserved_evaluation_task_ids())
    if eval_size_override is not None:
        reserved_ids = reserved_ids[:eval_size_override]
    eval_tasks = {task_id: evaluation_tasks_pool[task_id] for task_id in reserved_ids}
    validation_ids = set(select_tier_tasks(evaluation_tasks_pool, "validation").keys())
    return eval_tasks, validation_ids


def _run_pretraining_phase(base_model, tokenizer, config, pretraining_tasks):
    # "steps", not "epoch": pretraining_num_epochs defaults to 1, so an
    # epoch-based strategy would only save a checkpoint at the very end,
    # giving no protection against a mid-epoch interruption. save_steps=500
    # targets roughly one checkpoint every few minutes at pilot scale (~150
    # tasks), enough to make a deliberate interrupt/resume test meaningful
    # without excessive checkpoint I/O overhead.
    pretraining_config = replace(
        config, checkpoint_output_dir=PRETRAINING_CHECKPOINT_DIR,
        checkpoint_save_strategy="steps", checkpoint_save_steps=500,
    )
    model = attach_fresh_lora(base_model, config)
    resume_from = find_resumable_checkpoint(PRETRAINING_CHECKPOINT_DIR)
    start = time.monotonic()
    model = pretrain_shared_adapter(model, tokenizer, pretraining_tasks, pretraining_config, resume_from_checkpoint=resume_from)
    pretraining_seconds = time.monotonic() - start
    model.save_pretrained(ADAPTER_DIR)
    detach_lora(model)
    return pretraining_seconds


def _run_evaluation_phase(base_model, tokenizer, config, eval_tasks):
    all_rows = []
    all_timings = []
    for task in eval_tasks.values():
        rows, timing = diagnose_task_with_per_attempt_conditional_mitigation(
            base_model, tokenizer, config, CONFIG_NAME, task,
            RAW_OUTPUT_ROOT / "evaluation", enable_conditional_escalation=True,
            adapter_dir=ADAPTER_DIR,
        )
        save_config_rows(f"{CONFIG_NAME}_{task.task_id}", rows, OUTPUT_ROOT / "evaluation")
        all_rows += rows
        all_timings.append(timing)
    return all_rows, all_timings


def _print_metrics_block(label, rows):
    print(f"[{label}] exact_match_rate_test={exact_match_rate(rows, split='test'):.4f}")
    print(f"[{label}] per_cell_accuracy_test={per_cell_accuracy_distribution(rows, split='test')}")
    print(f"[{label}] far_outlier_tasks={far_outlier_task_ids(rows)}")


def _print_summary(all_rows, all_timings, validation_ids, pretraining_size, pretraining_seconds):
    ttt_total_seconds = sum(t.total_seconds for t in all_timings)
    print(f"pretraining_tasks={pretraining_size}")
    print(f"eval_tasks_measured={len(all_timings)}")
    print(f"pretraining_seconds={pretraining_seconds:.2f}")
    print(f"ttt_total_seconds={ttt_total_seconds:.2f}")
    print(f"pilot_total_seconds={(pretraining_seconds + ttt_total_seconds):.2f}")
    _print_metrics_block("reserved_all", all_rows)
    validation_only_rows = [r for r in all_rows if r.task_id in validation_ids]
    _print_metrics_block("validation_tier_only_vs_adr_0034", validation_only_rows)


def main() -> None:
    pretraining_size = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PRETRAINING_TASK_COUNT
    eval_size_override = int(sys.argv[2]) if len(sys.argv) > 2 else None

    config = _consolidated_config()
    base_model, tokenizer = load_base_model(config)

    pretraining_tasks = _select_pretraining_tasks(pretraining_size)
    pretraining_seconds = _run_pretraining_phase(base_model, tokenizer, config, pretraining_tasks)

    eval_tasks, validation_ids = _select_eval_tasks(eval_size_override)
    all_rows, all_timings = _run_evaluation_phase(base_model, tokenizer, config, eval_tasks)

    print(render_markdown(all_rows))
    print()
    print(render_timing_markdown(all_timings))
    print()
    _print_summary(all_rows, all_timings, validation_ids, len(pretraining_tasks), pretraining_seconds)


if __name__ == "__main__":
    main()
