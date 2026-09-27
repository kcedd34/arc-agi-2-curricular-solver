"""One task through the discovery engine (ADR 0110): derived search with the
generated properties on, then the antifraud verdict on every verified hit.
Returns predictions only; the gabarito is compared elsewhere (RN-CUR-03)."""
import time
from typing import List, NamedTuple, Optional

import numpy as np

from src.curriculum.discovery import session
from src.curriculum.discovery.antifraud import judge
from src.curriculum.discovery.library_index import library_indices
from src.curriculum.discovery.profile import profile_key
from src.curriculum.grid import Grid
from src.curriculum.library.derived.search import verified_derived_candidates_with_predictions
from src.curriculum.loader import Task
from src.curriculum.spec._generated import PREFIX


class Hit(NamedTuple):
    description: str
    uses_generated: bool
    indices: List[int]
    positions: List[int]
    accepted: bool
    reasons: List[str]
    predictions: List[Grid]


class TaskRun(NamedTuple):
    task_id: str
    profile: str
    seconds: float
    units: int
    hits: List[Hit]
    error: Optional[str] = None


def enumeration_positions(indices: List[int], profile: str) -> List[int]:
    """Rank of each library entry in the order this task was enumerated."""
    registry = session.active_registry()
    if registry is None:
        return list(indices)
    order = registry.ordered_indices(profile)
    return [int(np.flatnonzero(order == index)[0]) for index in indices]


def _hit(task: Task, profile: str, composition, predictions, effects: int) -> Hit:
    text = composition.describe()
    verdict = judge(task, composition, effects)
    indices = library_indices(text)
    return Hit(text, PREFIX in text, indices, enumeration_positions(indices, profile), verdict.accepted, verdict.reasons, predictions)


def run_task(task: Task) -> TaskRun:
    profile = profile_key(task)
    session.begin_trace()
    start = time.perf_counter()
    try:
        verified = verified_derived_candidates_with_predictions(task)
        effects = session.effects_tested()
        hits = [_hit(task, profile, comp, preds, effects) for comp, preds in verified]
        error = None
    except Exception as exc:  # a crash is a task result, never a batch abort
        hits, error = [], f"{type(exc).__name__}: {exc}"
    seconds = time.perf_counter() - start
    return TaskRun(task.task_id, profile, seconds, len(session.take_trace()), hits, error)
