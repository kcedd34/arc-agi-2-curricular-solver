"""Resumes ADR 0039's pilot v2 run after a deliberate interruption to fix
a bug in attach_pretrained_lora (see lora_setup.py's docstring): the
interrupted run had already produced complete, valid baseline results and
a complete, valid pretrained adapter, both reused here unchanged. Only the
warm-started scenario is re-run.

The interrupted run's own warm-started measurements are discarded, not
reused: they were produced by the broken attach_pretrained_lora, which ran
~55-70x slower per training step than it should, so their timing is not
valid data for the paired time comparison. Re-running is cheap with the
fix in place (comparable cost to the baseline scenario), so this keeps
both scenarios' timing directly comparable rather than mixing execution
paths.

Usage: python -m src.evaluation.resume_cross_task_pretraining_pilot_v2
"""
import json
from pathlib import Path
from typing import List

from src.evaluation.diagnostic_runner import render_timing_markdown
from src.evaluation.per_attempt_conditional_mitigation_pair_diagnostics import (
    PerAttemptConditionalMitigationPairRow,
    diagnose_task_with_per_attempt_conditional_mitigation,
    render_markdown,
    save_config_rows,
)
from src.evaluation.run_cross_task_pretraining_pilot_v2 import (
    ADAPTER_DIR,
    BASELINE_CONFIG_NAME,
    EVAL_SPLIT_MANIFEST_PATH,
    OUTPUT_ROOT,
    RAW_OUTPUT_ROOT,
    WARM_START_CONFIG_NAME,
    _consolidated_config,
    _print_scenario_summary,
)
from src.evaluation.validation_run_summary import exact_match_rate, per_cell_accuracy_distribution
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"

# Verbatim from outputs/logs/pilot_v2_run.log, the interrupted run's own
# printed summary for the phases this script does not re-run.
REUSED_BASELINE_TTT_TOTAL_SECONDS = 2338.68
REUSED_PRETRAINING_TASK_COUNT = 40
REUSED_PRETRAINING_SECONDS = 2330.73


def _load_eval_tasks():
    task_ids = json.loads(EVAL_SPLIT_MANIFEST_PATH.read_text(encoding="utf-8"))
    evaluation_tasks_pool = load_task_set(DATA_ROOT / "evaluation")
    return {task_id: evaluation_tasks_pool[task_id] for task_id in task_ids}


def _load_baseline_rows() -> List[PerAttemptConditionalMitigationPairRow]:
    baseline_dir = OUTPUT_ROOT / BASELINE_CONFIG_NAME
    rows = []
    for path in sorted(baseline_dir.glob(f"{BASELINE_CONFIG_NAME}_*.json")):
        rows += [PerAttemptConditionalMitigationPairRow(**r) for r in json.loads(path.read_text(encoding="utf-8"))]
    return rows


def _print_reused_baseline_summary(baseline_rows) -> None:
    print(f"[{BASELINE_CONFIG_NAME}] exact_match_rate_test={exact_match_rate(baseline_rows, split='test'):.4f} (reused from interrupted run)")
    print(f"[{BASELINE_CONFIG_NAME}] per_cell_accuracy_test={per_cell_accuracy_distribution(baseline_rows, split='test')} (reused from interrupted run)")
    print(f"[{BASELINE_CONFIG_NAME}] ttt_total_seconds={REUSED_BASELINE_TTT_TOTAL_SECONDS:.2f} (reused from interrupted run)")
    print(f"pretraining_tasks={REUSED_PRETRAINING_TASK_COUNT} (reused adapter, not re-pretrained)")
    print(f"pretraining_seconds={REUSED_PRETRAINING_SECONDS:.2f} (reused from interrupted run)")


def _run_warm_started_scenario(base_model, tokenizer, config, eval_tasks):
    all_rows: List[PerAttemptConditionalMitigationPairRow] = []
    all_timings = []
    for task in eval_tasks.values():
        rows, timing = diagnose_task_with_per_attempt_conditional_mitigation(
            base_model, tokenizer, config, WARM_START_CONFIG_NAME, task,
            RAW_OUTPUT_ROOT / WARM_START_CONFIG_NAME, enable_conditional_escalation=True,
            adapter_dir=ADAPTER_DIR,
        )
        save_config_rows(f"{WARM_START_CONFIG_NAME}_{task.task_id}", rows, OUTPUT_ROOT / WARM_START_CONFIG_NAME)
        all_rows += rows
        all_timings.append(timing)
    return all_rows, all_timings


def main() -> None:
    from src.solvers.neural.model_loader import load_base_model

    config = _consolidated_config()
    base_model, tokenizer = load_base_model(config)
    eval_tasks = _load_eval_tasks()

    baseline_rows = _load_baseline_rows()
    print(f"[resume] reused {len(baseline_rows)} baseline pair rows across {len(eval_tasks)} tasks from the interrupted run")
    _print_reused_baseline_summary(baseline_rows)

    warm_rows, warm_timings = _run_warm_started_scenario(base_model, tokenizer, config, eval_tasks)
    print(render_markdown(warm_rows))
    print(render_timing_markdown(warm_timings))
    _print_scenario_summary(WARM_START_CONFIG_NAME, warm_rows, warm_timings)


if __name__ == "__main__":
    main()
