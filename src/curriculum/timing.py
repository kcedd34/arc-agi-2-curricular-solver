"""Wall-clock instrumentation for batch diagnostic runs (continuous-loop.md
Fase A.4/E.4: "registre tempo total, tempo medio e maximo por tarefa").
Kept separate from `parallel_batch.py` so `run_batch`'s existing callers
(candidate_hit_rate.py, object_pack_gate.py, piece_usage_audit.py,
scale_test.py, two_attempt.py) are untouched; only the Fase A/E callers
(candidate_probe.py, probe.py) opt in via the `_timed` variants below.
"""
import functools
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Tuple, TypeVar

T = TypeVar("T")


@dataclass
class TimedResult:
    value: Any
    elapsed_seconds: float


@dataclass(frozen=True)
class RunTiming:
    wall_seconds: float
    mean_task_seconds: float
    max_task_seconds: float
    num_timed: int
    median_task_seconds: float = 0.0
    slowest_task_id: str = ""
    per_task_seconds: Dict[str, float] = field(default_factory=dict)


def _timed_call(worker_fn: Callable[[str], T], item_id: str) -> TimedResult:
    start = time.perf_counter()
    value = worker_fn(item_id)
    return TimedResult(value=value, elapsed_seconds=time.perf_counter() - start)


def with_timing(worker_fn: Callable[[str], T]) -> Callable[[str], TimedResult]:
    """Wrap a `run_batch` worker so each call's own elapsed time travels
    with its result. A worker that raises is left to `run_batch`'s
    existing per-item isolation (the raw exception, untimed).

    Returns a `functools.partial` bound to the module-level `_timed_call`,
    not a local closure: `run_batch`'s parallel path pickles the worker
    to send it to a `ProcessPoolExecutor` worker process, and a closure
    defined inside this function has no importable qualified name, so
    pickling it raises `AttributeError` (caught 2026-09-23 the hard way,
    Round 2 Fase A: 200/200 tasks errored in 0.07s wall time)."""
    return functools.partial(_timed_call, worker_fn)


def summarize_durations(durations: Dict[str, float], wall_seconds: float) -> RunTiming:
    """RN-CUR-38: every measurement reports mean, median, max and the id of
    the slowest task, and keeps the per-task times."""
    if not durations:
        return RunTiming(wall_seconds=wall_seconds, mean_task_seconds=0.0, max_task_seconds=0.0, num_timed=0)
    values = sorted(durations.values())
    middle = len(values) // 2
    median = values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2
    return RunTiming(
        wall_seconds=wall_seconds,
        mean_task_seconds=sum(values) / len(values),
        max_task_seconds=values[-1],
        num_timed=len(values),
        median_task_seconds=median,
        slowest_task_id=max(durations, key=durations.get),
        per_task_seconds=dict(durations),
    )


def summarize_timing(outcomes: List[Tuple[str, Any]], wall_seconds: float) -> RunTiming:
    """`wall_seconds` is the real elapsed time of the whole batch call
    (parallel workers overlap, so it is not the sum of per-task times);
    statistics are computed only over items that actually produced a
    `TimedResult` (errored items carry no timing, RN-CUR-30: do not
    infer a time for work that did not complete)."""
    durations = {tid: o.elapsed_seconds for tid, o in outcomes if isinstance(o, TimedResult)}
    return summarize_durations(durations, wall_seconds)
