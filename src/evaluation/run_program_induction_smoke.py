"""Smoke test of ADR 0060's induce-verify-apply program-induction path
against 007bbfb7, this project's own original neural-solver smoke-test
task (see CLAUDE.md Section 6), a task with a genuinely short ground-truth
rule (roughly six lines of Python).

Pre-registered proceed/abandon criteria (ADR 0060):
- Proceed: at least 1 sampled completion, after induce-verify, reproduces
  all 5 train pairs (whether it also gets the held-out test pair right is
  secondary at this tier).
- Abandon: zero verified programs across every sampled completion.

This is a `smoke`-tier result (Golden Rule 7): it can justify proceeding
to the next diagnostic step, but never a policy/architecture decision on
its own; that needs a `validation`-tier run (30-50 tasks).

**Corrected-retry design, 2026-09-19:** `--model` overrides
`NeuralSolverConfig.model_name` for this run only (the production
default stays `Qwen/Qwen3-4B-Base` per ADR 0055 unless this flag is
passed), and `--num-candidates` overrides `sample_program_completions`'s
k, so the same script can test both the higher-k retry and the
alternative Instruct model without touching the production config.

**Ceiling bug found and fixed, same day:** the first k=96 attempt reused
`NEURAL_TASK_CEILING_SECONDS` (400s), the production per-task ceiling
sized for one task's TTT+generation, unmodified. This diagnostic instead
samples k candidates serially with no TTT, so its own time scales with k;
at 400s the run was aborted by the circuit breaker after only ~14/96
candidates, an aborted run, not a real k=96 result. `--ceiling-seconds`
now lets this script's ceiling scale independently of the production
constant.

Usage:
  python -m src.evaluation.run_program_induction_smoke
  python -m src.evaluation.run_program_induction_smoke --num-candidates 96 --ceiling-seconds 3600
  python -m src.evaluation.run_program_induction_smoke --model Qwen/Qwen3-4B-Instruct-2507
"""
import argparse
from pathlib import Path

from src.evaluation.task_time_limit import (
    NEURAL_TASK_CEILING_SECONDS,
    TaskTimeExceeded,
    TaskTimeLimiter,
)
from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.model_loader import load_base_model
from src.solvers.neural.program_generation import DEFAULT_NUM_CANDIDATES, sample_program_completions
from src.solvers.neural.program_induction import apply_program_to_test, induce_verified_program
from src.utils.task_loader import load_task

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TASK_PATH = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data" / "training" / "007bbfb7.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=None, help="Override NeuralSolverConfig.model_name")
    parser.add_argument("--num-candidates", type=int, default=DEFAULT_NUM_CANDIDATES)
    parser.add_argument(
        "--ceiling-seconds",
        type=float,
        default=NEURAL_TASK_CEILING_SECONDS,
        help="Circuit-breaker ceiling for this run; scale with --num-candidates "
        "(unlike production, this script has no TTT, only k serial samples)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    task = load_task(TASK_PATH)
    print(f"Task {task.task_id}: {len(task.train)} train pairs, {len(task.test)} test pairs")

    config = NeuralSolverConfig()
    if args.model is not None:
        config.model_name = args.model
    print(f"Model: {config.model_name}, num_candidates: {args.num_candidates}")

    model, tokenizer = load_base_model(config)

    limiter = TaskTimeLimiter(ceiling_seconds=args.ceiling_seconds)
    limiter.start()
    try:
        completions = sample_program_completions(
            model, tokenizer, task, num_candidates=args.num_candidates, limiter=limiter
        )
    except TaskTimeExceeded as exc:
        print(f"[ABORTED BY CIRCUIT BREAKER] {exc}")
        print("Verdict: ABANDON (no completions sampled before the ceiling)")
        return

    for i, completion in enumerate(completions):
        print(f"--- completion {i} ---")
        print(completion)

    result = induce_verified_program(completions, task)
    print(f"Verified programs: {len(result.verified_programs)}")
    print(f"Ambiguous: {result.is_ambiguous}")

    if not result.verified_programs:
        print("Verdict: ABANDON (zero verified programs reproduced all 5 train pairs)")
        return

    print("Verdict: PROCEED (at least 1 program reproduced all 5 train pairs)")
    for program in result.verified_programs:
        print("--- verified program ---")
        print(program)

    if result.chosen_program is not None:
        predicted = apply_program_to_test(result.chosen_program, task)
        actual = [pair.output for pair in task.test]
        print(f"Predicted test output: {predicted}")
        print(f"Actual test output: {actual}")
        print(f"Test pair(s) exact match: {predicted == actual}")


if __name__ == "__main__":
    main()
