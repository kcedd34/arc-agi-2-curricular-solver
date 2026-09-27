"""One batch of the closed loop (ADR 0110): the registry is frozen while the
batch runs (workers agree on the enumeration order), then updated from the
results in task-id order, so the whole loop is deterministic."""
from typing import List

from src.curriculum.discovery import session
from src.curriculum.discovery.loop_tasks import TRAINING_DIR
from src.curriculum.discovery.registry import Registry
from src.curriculum.discovery.run_task import TaskRun, run_task
from src.curriculum.loader import load_task
from src.curriculum.parallel_batch import run_batch


def solve_worker(task_id: str) -> TaskRun:
    return run_task(load_task(TRAINING_DIR / f"{task_id}.json"))


def crashed(task_id: str, error: BaseException) -> TaskRun:
    return TaskRun(task_id, "", 0.0, 0, [], f"{type(error).__name__}: {error}")


def run_frozen_batch(task_ids: List[str], registry: Registry, workers: int) -> List[TaskRun]:
    session.set_registry(registry)
    outcomes = run_batch(task_ids, solve_worker, workers)
    return [crashed(task_id, out) if isinstance(out, BaseException) else out for task_id, out in outcomes]


def credit_registry(registry: Registry, runs: List[TaskRun]) -> None:
    """Fold one finished batch into the registry, in task order."""
    for run in sorted(runs, key=lambda r: r.task_id):
        if run.error or not run.profile:
            continue
        evaluated = registry.ordered_indices(run.profile)[: run.units]
        credited = [i for hit in run.hits if hit.accepted for i in hit.indices]
        failed = [i for hit in run.hits if not hit.accepted for i in hit.indices]
        registry.record_task(run.profile, evaluated, credited, failed)


def split_batches(task_ids: List[str], size: int) -> List[List[str]]:
    return [task_ids[i : i + size] for i in range(0, len(task_ids), size)]


def snapshot_name(prefix: str, batch_number: int) -> str:
    return f"{prefix}-batch{batch_number:02d}"
