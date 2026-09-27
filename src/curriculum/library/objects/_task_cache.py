"""Single-entry, per-task cache for values that are pure functions of a
task's grids (ADR 0090). Keyed by a content fingerprint, not by object
identity, because callers reload the same task from disk. It stores
already-computed results only; it never changes what is computed."""
import hashlib
import json
from typing import Any, Callable, Dict, Tuple

from src.curriculum.loader import Task

_STATE: Dict[str, Any] = {"key": None, "values": {}}


def task_fingerprint(task: Task) -> str:
    payload = json.dumps([task.task_id, task.train, task.test_inputs], default=list)
    return hashlib.sha256(payload.encode()).hexdigest()


def cached_for_task(task: Task, name: str, builder: Callable[[], Any]) -> Any:
    key = task_fingerprint(task)
    if _STATE["key"] != key:
        _STATE["key"] = key
        _STATE["values"] = {}
    values = _STATE["values"]
    if name not in values:
        values[name] = builder()
    return values[name]


def clear_task_cache() -> None:
    _STATE["key"] = None
    _STATE["values"] = {}
