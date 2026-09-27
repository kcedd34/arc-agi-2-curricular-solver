"""Widened budgets for the one-off oracle measurement (ADR 0111). The solver
constants are restored on exit, so the widening never outlives the measurement."""
from contextlib import contextmanager

from src.curriculum.discovery import task_generated
from src.curriculum.search.sequence import budget

ENTRY_BUDGET = 10_000_000
MAX_SELECTIONS = 3000
SEQUENCE_UNITS = 600_000_000
SEQUENCE_SECONDS = 1800.0
FIRST_STAGE_LIMIT = 60


@contextmanager
def widened_budgets():
    saved = (task_generated.ENTRY_BUDGET, task_generated.MAX_SELECTIONS, budget.SEQUENCE_UNIT_BUDGET, budget.SEQUENCE_DEADLINE_SECONDS)
    task_generated.ENTRY_BUDGET, task_generated.MAX_SELECTIONS = ENTRY_BUDGET, MAX_SELECTIONS
    budget.SEQUENCE_UNIT_BUDGET, budget.SEQUENCE_DEADLINE_SECONDS = SEQUENCE_UNITS, SEQUENCE_SECONDS
    try:
        yield
    finally:
        task_generated.ENTRY_BUDGET, task_generated.MAX_SELECTIONS = saved[0], saved[1]
        budget.SEQUENCE_UNIT_BUDGET, budget.SEQUENCE_DEADLINE_SECONDS = saved[2], saved[3]
