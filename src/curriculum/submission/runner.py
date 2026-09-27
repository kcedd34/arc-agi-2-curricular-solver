"""Runs the solver over many tasks in isolated processes.

Each task gets its own process so a hard per-task timeout can kill it
(a process pool cannot), and a global wall budget stops launching new
tasks; every task without a result falls back to the ADR 0011 net later.
"""
import multiprocessing
import time
from collections import deque
from dataclasses import dataclass
from multiprocessing.connection import wait
from typing import Callable, Dict, List, Optional

from src.curriculum.loader import Task

POLL_SECONDS = 0.5


@dataclass
class TaskOutcome:
    task_id: str
    status: str  # ok | error | timeout | skipped_budget
    attempts: Optional[list] = None
    seconds: float = 0.0
    error: Optional[str] = None


@dataclass
class _Running:
    task_id: str
    process: object
    conn: object
    started: float


def _context():
    methods = multiprocessing.get_all_start_methods()
    return multiprocessing.get_context("fork" if "fork" in methods else "spawn")


def _child(conn, solve_fn: Callable, task: Task) -> None:
    try:
        message = ("ok", solve_fn(task))
    except BaseException as exc:  # isolated per-task failure
        message = ("error", repr(exc))
    conn.send(message)
    conn.close()


def _launch(ctx, solve_fn: Callable, task: Task, clock: Callable) -> _Running:
    parent, child = ctx.Pipe(duplex=False)
    process = ctx.Process(target=_child, args=(child, solve_fn, task), daemon=True)
    process.start()
    child.close()
    return _Running(task.task_id, process, parent, clock())


def _collect(run: _Running, clock: Callable) -> TaskOutcome:
    seconds = clock() - run.started
    try:
        status, payload = run.conn.recv()
    except EOFError:
        status, payload = "error", "worker exited without a result"
    run.process.join()
    run.conn.close()
    if status == "ok":
        return TaskOutcome(run.task_id, "ok", payload, seconds)
    return TaskOutcome(run.task_id, "error", None, seconds, payload)


def _kill(run: _Running, clock: Callable) -> TaskOutcome:
    run.process.kill()
    run.process.join()
    run.conn.close()
    return TaskOutcome(run.task_id, "timeout", None, clock() - run.started)


def _harvest(running: List[_Running], per_task: float, clock: Callable) -> List[TaskOutcome]:
    ready = set(wait([r.conn for r in running], timeout=POLL_SECONDS))
    outcomes = []
    for run in list(running):
        if run.conn in ready:
            outcomes.append(_collect(run, clock))
        elif clock() - run.started > per_task:
            outcomes.append(_kill(run, clock))
        else:
            continue
        running.remove(run)
    return outcomes


def run_tasks(tasks: Dict[str, Task], solve_fn: Callable, workers: int, per_task_seconds: float,
              global_seconds: float, clock: Callable = time.monotonic) -> Dict[str, TaskOutcome]:
    ctx, begin = _context(), clock()
    pending, running, results = deque(_cheapest_first(tasks)), [], {}
    while pending or running:
        while pending and len(running) < workers and clock() - begin < global_seconds:
            running.append(_launch(ctx, solve_fn, tasks[pending.popleft()], clock))
        if not running:
            break
        for outcome in _harvest(running, per_task_seconds, clock):
            results[outcome.task_id] = outcome
    for task_id in pending:
        results[task_id] = TaskOutcome(task_id, "skipped_budget")
    return results


def _cheapest_first(tasks: Dict[str, Task]) -> List[str]:
    """Small grids first, so a global cut lands on the costliest tasks."""
    return sorted(tasks, key=lambda tid: (_cells(tasks[tid]), tid))


def _cells(task: Task) -> int:
    grids = [p.input for p in task.train] + [p.output for p in task.train] + list(task.test_inputs)
    return sum(len(g) * len(g[0]) for g in grids if g)
