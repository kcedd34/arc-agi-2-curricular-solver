"""Smoke-tier (2-task) mechanical check that ADR 0058's circuit breaker
wiring in per_attempt_conditional_mitigation_pair_diagnostics.py behaves
correctly on real GPU hardware, before scaling to the ADR 0057 pilot
(100-150 tasks).

Mirrors neural_solver.solve_task's production pattern (a fresh
TaskTimeLimiter per task, TaskTimeExceeded caught at the per-task loop
level, TimeLimitAbortTracker recording aborts) instead of
run_per_attempt_conditional_mitigation_smoke.py, which never passed a
limiter at all and so never exercised this wiring on GPU.

Usage: python -m src.evaluation.run_circuit_breaker_smoke [training|evaluation]

Diagnostic only: confirms the breaker fires/doesn't-fire correctly on
whichever 2 tasks the "smoke" tier actually selects from the given
split, does not itself validate any accuracy or timing claim about the
pilot.

Real run result (evaluation split, 2026-09-18): the smoke tier's first
alphabetical task is actually 0934a4d8, not 135a2760/136b0064 as
originally assumed when this file was written; sample_tiers.py sorts by
raw task_id string, where "0934a4d8" sorts before "135a2760" (digit '0'
< '1'). 0934a4d8 is the same known slow outlier documented in ADR
0028/0049 (it hit the 400s ceiling on real Kaggle hardware too, ADR
0049's "genuine round 4"/kernel v9 sections); it correctly aborted here
at elapsed=400.07s, matching that history almost exactly. 135a2760
completed normally (341.24s total, no abort). Zero unhandled exceptions,
exit code 0.
"""
import sys
from pathlib import Path

from src.evaluation.diagnostic_runner import render_timing_markdown
from src.evaluation.per_attempt_conditional_mitigation_pair_diagnostics import (
    diagnose_task_with_per_attempt_conditional_mitigation,
    render_markdown,
    save_config_rows,
)
from src.evaluation.sample_tiers import select_tier_tasks
from src.evaluation.task_time_limit import (
    NEURAL_TASK_CEILING_SECONDS,
    TaskTimeExceeded,
    TaskTimeLimiter,
    TimeLimitAbortTracker,
)
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.model_loader import load_base_model
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "circuit_breaker_smoke"
RAW_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "raw_generations" / "circuit_breaker_smoke"
CONFIG_NAME = "conditional_per_attempt_with_breaker"


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    base_model, tokenizer = load_base_model(NeuralSolverConfig())
    all_tasks = load_task_set(DATA_ROOT / split)
    smoke_tasks = select_tier_tasks(all_tasks, "smoke")
    baseline_config = NeuralSolverConfig()
    aborts = TimeLimitAbortTracker()

    all_rows = []
    all_timings = []
    for task in smoke_tasks.values():
        limiter = TaskTimeLimiter(ceiling_seconds=NEURAL_TASK_CEILING_SECONDS)
        limiter.start()
        try:
            rows, timing = diagnose_task_with_per_attempt_conditional_mitigation(
                base_model, tokenizer, baseline_config, CONFIG_NAME, task, RAW_OUTPUT_ROOT / split,
                enable_conditional_escalation=True, limiter=limiter,
            )
        except TaskTimeExceeded:
            aborts.record_abort(task.task_id)
            print(f"[ABORTED BY CIRCUIT BREAKER] task={task.task_id} elapsed={limiter.elapsed():.2f}s")
            continue
        save_config_rows(f"circuit_breaker_smoke_{CONFIG_NAME}_{task.task_id}", rows, OUTPUT_ROOT / split)
        all_rows += rows
        all_timings.append(timing)

    print(render_markdown(all_rows))
    print()
    print(render_timing_markdown(all_timings))
    print()
    print(f"Tasks aborted by circuit breaker: {sorted(aborts.aborted_task_ids)}")


if __name__ == "__main__":
    main()
