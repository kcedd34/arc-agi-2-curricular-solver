"""Verifies a candidate transform(g) program against a task's own train
pairs (ADR 0060), reusing ADR 0038's ambiguity bar: a candidate only
counts if it reproduces 100% of the train pairs, never resolved by
picking one arbitrarily when more than one survives.
"""
from typing import List, Optional

from src.solvers.neural.grid_serialization import grid_to_text, text_to_grid
from src.solvers.neural.program_sandbox import run_program
from src.utils.grid_types import Grid
from src.utils.task_loader import Pair


def run_program_on_grid(program_source: str, grid: Grid) -> Optional[Grid]:
    rows = grid_to_text(grid).split("\n")
    result_rows = run_program(program_source, rows)
    if result_rows is None:
        return None
    return text_to_grid("\n".join(result_rows))


def verify_program_against_train_pairs(program_source: str, train: List[Pair]) -> bool:
    return all(
        run_program_on_grid(program_source, pair.input) == pair.output
        for pair in train
    )
