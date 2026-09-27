"""Aggregate sanity checks before a stage transition, PRD Section 9.1.

Two independent checks: does the persisted state document have values
this code can trust (a schema/value check, catches hand-edited
outputs/curriculum/state.json drift), and have any already-solved
tasks regressed (regression.py, a real search_task re-run, not free).
"""
from dataclasses import dataclass
from typing import List

from src.curriculum.regression import RegressionResult, run_regression
from src.curriculum.state import CurriculumState

VALID_STAGES = {f"stage_{n}" for n in range(8)}
VALID_STAGE_STATUSES = {"in_progress", "complete", "blocked"}


@dataclass
class ValidationResult:
    schema_errors: List[str]
    regression: RegressionResult

    @property
    def is_valid(self) -> bool:
        return not self.schema_errors and not self.regression.regressed


def validate_state_schema(state: CurriculumState) -> List[str]:
    errors = []
    if state.schema_version != 1:
        errors.append(f"unexpected schema_version: {state.schema_version}")
    if state.current_stage not in VALID_STAGES:
        errors.append(f"unexpected current_stage: {state.current_stage}")
    if state.stage_status not in VALID_STAGE_STATUSES:
        errors.append(f"unexpected stage_status: {state.stage_status}")
    if state.next_task and state.next_task in state.solved_tasks:
        errors.append(f"next_task {state.next_task!r} is already in solved_tasks")
    return errors


def validate_state(state: CurriculumState) -> ValidationResult:
    schema_errors = validate_state_schema(state)
    regression = run_regression(state.solved_tasks)
    return ValidationResult(schema_errors=schema_errors, regression=regression)
