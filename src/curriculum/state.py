"""Typed load/save for outputs/curriculum/state.json, PRD Section 9.1.

The schema mirrors what Stage 0 scaffolding already wrote by hand
(docs/curriculum/progress.md rows 1-16): a flat, versioned JSON document
tracking curriculum progress across restarts, never derived by
re-running search or from git history.
"""
import dataclasses
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_STATE_PATH = Path("outputs/curriculum/state.json")


@dataclass
class PartitionRef:
    path: str
    seed: int
    total_training_tasks: int
    curricular_pool_size: int
    probe_pool_size: int
    pinned_curricular_task_ids: List[str]


@dataclass
class CurriculumState:
    """`library_version` and `next_step` are set by hand at the end of a
    session, mirroring what BOOTSTRAP.md Section 9.2 already expects of the
    desk-check artifact and what docs/curriculum/tasks/stage-3-prep.md's
    consolidated step list tracks in prose; this keeps the same numbers in
    the machine-readable state, not just in progress.md's free text."""

    schema_version: int
    updated_at: str
    current_stage: str
    stage_status: str
    partition_ref: PartitionRef
    remaining_stage_0_items: List[str]
    blocked_on: List[str]
    solved_tasks: List[str]
    next_task: str
    probe_pool_checkpoints: List[Dict[str, Any]]
    library_version: str
    next_step: int
    object_pack: Dict[str, Any] = field(default_factory=dict)


def load_state(path: Path = DEFAULT_STATE_PATH) -> CurriculumState:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    raw = dict(raw)
    raw["partition_ref"] = PartitionRef(**raw["partition_ref"])
    return CurriculumState(**raw)


def save_state(state: CurriculumState, path: Path = DEFAULT_STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(state)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")


def mark_task_solved(state: CurriculumState, task_id: str, updated_at: str) -> CurriculumState:
    """Return a new state with task_id appended to solved_tasks, idempotently."""
    if task_id in state.solved_tasks:
        return state
    solved_tasks = state.solved_tasks + [task_id]
    return dataclasses.replace(state, solved_tasks=solved_tasks, updated_at=updated_at)
