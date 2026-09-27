"""One-line and file renderings of a `RunTiming` (RN-CUR-38)."""
import json
from pathlib import Path

from src.curriculum.timing import RunTiming


def timing_line(timing: RunTiming, workers: int = None) -> str:
    suffix = f" workers={workers}" if workers is not None else ""
    return (
        f"wall={timing.wall_seconds:.1f}s mean={timing.mean_task_seconds:.2f}s "
        f"median={timing.median_task_seconds:.2f}s max={timing.max_task_seconds:.1f}s "
        f"({timing.slowest_task_id or '-'}) n={timing.num_timed}{suffix}"
    )


def write_task_times(path: Path, timing: RunTiming) -> Path:
    """Per-task times, slowest first, so the tail can be inspected."""
    ranked = sorted(timing.per_task_seconds.items(), key=lambda kv: -kv[1])
    payload = {"summary": timing_line(timing), "per_task_seconds": dict(ranked)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
