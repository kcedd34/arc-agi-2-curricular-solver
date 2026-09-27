"""Run a task through search and package a human-reviewable desk-check result.

RN-CUR-14: gives a human enough to audit a solved task's reasoning (which
composition, which params, how many trace steps per train pair) without
ever dumping a raw grid, keeping review scoped and fast. By design this
module stays gabarito-blind (RN-CUR-14), so it can never itself decide
the real `solved` verdict (RN-CUR-04's two-attempt, gabarito-checked
policy, computed in `verified_verdict.py`); `status`/`unanimous` here
only describe candidate agreement, never gabarito correctness (2026-09-22
correction, after `status == "solved"` was mistaken for that elsewhere).
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple

from typing import Any

from src.curriculum.grid import grid_dims
from src.curriculum.loader import Task
from src.curriculum.search.rank import SearchResult, search_task
from src.curriculum.search.sequence.composition import run_candidate


@dataclass
class CandidateTrace:
    candidate: Any  # Composition or ObjectComposition
    steps_per_train_pair: List[int]


@dataclass
class DeskCheckReport:
    task_id: str
    status: str
    unanimous: bool
    verified: List[Any]  # Composition and/or ObjectComposition
    candidate_traces: List[CandidateTrace]
    prediction_shapes: Optional[List[Tuple[int, int]]]


def _trace_step_counts(candidate: Any, task: Task) -> List[int]:
    """`result.verified` can hold any candidate type, including two-rule
    sequences (ADR 0097); `run_candidate` dispatches on type."""
    return [len(run_candidate(candidate, pair.input)[1]) for pair in task.train]


def run_desk_check(task: Task) -> DeskCheckReport:
    result: SearchResult = search_task(task)

    candidate_traces = [
        CandidateTrace(candidate=c, steps_per_train_pair=_trace_step_counts(c, task))
        for c in result.verified
    ]

    prediction_shapes = None
    if result.predictions is not None:
        prediction_shapes = [grid_dims(grid) for grid in result.predictions]

    return DeskCheckReport(
        task_id=task.task_id,
        status=result.status,
        unanimous=result.status == "solved",
        verified=result.verified,
        candidate_traces=candidate_traces,
        prediction_shapes=prediction_shapes,
    )
