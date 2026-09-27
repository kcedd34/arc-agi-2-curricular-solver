"""Follow-up to ADR 0030: after finding no_repeat_ngram_size=3 alone (not
repetition_penalty) drives both the failure-mode fix and the held-out-
accuracy regression, tries a looser no_repeat_ngram_size=5 (no
repetition_penalty) on the same 8-task sanity sample, to see whether a
gentler block still fixes the two target tasks with less collateral
damage on the other 6.

Usage: python -m src.evaluation.run_gentle_ngram_smoke [training|evaluation]

Diagnostic only, does not decide production-default status, see
docs/decisions/0030-splitting-repetition-mitigation-parameters.md.
"""
import sys
from pathlib import Path

from src.evaluation.decoding_mitigation_configs import build_gentle_ngram_config
from src.evaluation.diagnostic_runner import render_timing_markdown
from src.evaluation.mitigation_diagnostics import diagnose_task_with_mitigations, render_markdown, save_config_rows
from src.evaluation.sample_tiers import select_tier_tasks
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.model_loader import load_base_model
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "gentle_ngram_smoke"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations" / "gentle_ngram_smoke"


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    base_model, tokenizer = load_base_model(NeuralSolverConfig())
    all_tasks = load_task_set(DATA_ROOT / split)
    sanity_tasks = select_tier_tasks(all_tasks, "sanity")
    config_name, config = build_gentle_ngram_config()[0]

    all_rows = []
    all_timings = []
    for task in sanity_tasks.values():
        rows, timing = diagnose_task_with_mitigations(
            base_model, tokenizer, config, config_name, task, RAW_OUTPUT_ROOT / split
        )
        save_config_rows(f"gentle_ngram_smoke_{config_name}_{task.task_id}", rows, OUTPUT_ROOT / split)
        all_rows += rows
        all_timings.append(timing)

    print(render_markdown(all_rows))
    print()
    print(render_timing_markdown(all_timings))


if __name__ == "__main__":
    main()
