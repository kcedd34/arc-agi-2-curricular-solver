"""Worst-case GPU memory smoke test: picks the evaluation-split task with the
most total grid cells (train+test, input+output) and runs one full TTT +
generation pass on it, reporting peak VRAM usage and, if any, the exact step
that ran out of memory (model load, TTT, or generation/sampling).

Usage: python -m src.evaluation.run_memory_smoke [split]

Does not implement any OOM mitigation; see the smoke-test-memory ADR for
next steps if this run reports an OOM.
"""
import json
import sys
from pathlib import Path

from src.evaluation.memory_smoke import run_memory_smoke_test
from src.evaluation.worst_case_task import find_largest_task
from src.solvers.neural.config import NeuralSolverConfig
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "diagnostics" / "memory_smoke_test"


def _report(result) -> str:
    lines = [
        f"task_id: {result.task_id}",
        f"oom_step: {result.oom_step or 'none'}",
        f"peak_vram_bytes: {result.peak_vram_bytes} ({result.peak_vram_bytes / 2**30:.2f} GiB)",
        f"total_vram_bytes: {result.total_vram_bytes} ({result.total_vram_bytes / 2**30:.2f} GiB)",
    ]
    if result.oom_step is None:
        headroom = result.total_vram_bytes - result.peak_vram_bytes
        lines.append(f"headroom_bytes: {headroom} ({headroom / 2**30:.2f} GiB)")
    return "\n".join(lines)


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    tasks = load_task_set(DATA_ROOT / split)
    task = find_largest_task(tasks)
    config = NeuralSolverConfig()

    result = run_memory_smoke_test(config, task)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / f"{split}_{task.task_id}.json").write_text(
        json.dumps(result.__dict__), encoding="utf-8"
    )
    print(_report(result))


if __name__ == "__main__":
    main()
