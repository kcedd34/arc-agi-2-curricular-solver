"""Generic process-pool batch runner for curricular batch drivers
(object_pack_gate.py, probe.py, scale_test.py), item 1 of the pending
2026-09-22 follow-up request.

Determinism: results are collected into a dict keyed by item_id as
futures complete (arbitrary order), then re-emitted in the caller's own
`item_ids` order, so the returned list never depends on which process
finished first. Isolation: a worker exception (raised despite the
caller's own per-item try/except, e.g. a pickling error) is caught here
too and returned as the `BaseException` instance itself, in place of a
normal result, instead of aborting the whole batch.
"""
import argparse
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Callable, List, Tuple, TypeVar, Union

T = TypeVar("T")
Outcome = Union[T, BaseException]


DEFAULT_WORKERS = 6  # RN-CUR-37: the single place the default lives
WORKERS_ENV = "CURRICULUM_WORKERS"


def _env_workers() -> int:
    raw = os.environ.get(WORKERS_ENV, "").strip()
    if not raw:
        return 0
    if not raw.isdigit() or int(raw) < 1:
        raise ValueError(f"{WORKERS_ENV} must be a positive integer, got {raw!r}")
    return int(raw)


def default_worker_count() -> int:
    """Env var `CURRICULUM_WORKERS` if set, else `DEFAULT_WORKERS` capped at
    the machine's core count."""
    return _env_workers() or max(1, min(DEFAULT_WORKERS, os.cpu_count() or 1))


def resolve_workers(cli_workers: int = None, sequential: bool = False) -> int:
    """Precedence: --sequential (1) > --workers N > env var > default."""
    if sequential:
        return 1
    if cli_workers is not None:
        if cli_workers < 1:
            raise ValueError(f"--workers must be >= 1, got {cli_workers}")
        return cli_workers
    return default_worker_count()


def add_worker_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workers", type=int, default=None, help="process count (env CURRICULUM_WORKERS, default 6)")
    parser.add_argument("--sequential", action="store_true", help="run in-process (same as --workers 1)")


def _safe_call(worker_fn: Callable[[str], T], item_id: str) -> Outcome:
    try:
        return worker_fn(item_id)
    except BaseException as exc:  # isolated per-item failure
        return exc


def _run_sequential(item_ids: List[str], worker_fn: Callable[[str], T]) -> List[Tuple[str, Outcome]]:
    return [(item_id, _safe_call(worker_fn, item_id)) for item_id in item_ids]


def _run_parallel(
    item_ids: List[str], worker_fn: Callable[[str], T], max_workers: int
) -> List[Tuple[str, Outcome]]:
    outcomes = {}
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {executor.submit(worker_fn, item_id): item_id for item_id in item_ids}
        for future in as_completed(future_to_id):
            item_id = future_to_id[future]
            try:
                outcomes[item_id] = future.result()
            except BaseException as exc:  # isolated per-item failure
                outcomes[item_id] = exc
    return [(item_id, outcomes[item_id]) for item_id in item_ids]


def run_batch(
    item_ids: List[str], worker_fn: Callable[[str], T], max_workers: int = None
) -> List[Tuple[str, Outcome]]:
    """Run `worker_fn(item_id)` for every id, in-process for a single item
    or `max_workers <= 1`, otherwise across `max_workers` processes. The
    returned list is always ordered exactly like `item_ids`, whichever
    path ran."""
    workers = max_workers if max_workers is not None else default_worker_count()
    if workers <= 1 or len(item_ids) <= 1:
        return _run_sequential(item_ids, worker_fn)
    return _run_parallel(item_ids, worker_fn, workers)
