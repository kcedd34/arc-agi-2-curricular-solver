"""Static undefined-name check for the self-contained Kaggle notebook.

`ast.parse` only validates syntax, it does not catch a name that is used
but never imported or defined anywhere (see ADR 0049's "Fourth round
attempt, notebook import bug found" section: `StoppingCriteriaList` was
used in Part C's generation cell but only `StoppingCriteria` was
imported in an earlier cell, and this passed `ast.parse` cleanly).

All notebook cells run in one shared namespace on Kaggle, top to bottom,
so this concatenates the cells into a single synthetic module (the same
semantics pyflakes needs to resolve a name defined in an earlier cell
and used in a later one) and runs pyflakes's undefined-name check
against that combined source.
"""
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from pyflakes.checker import Checker
from pyflakes.messages import UndefinedName

from src.evaluation.notebook_cells import extract_code_cells


@dataclass(frozen=True)
class UndefinedNameIssue:
    cell_index: int
    line: int
    message: str


def concatenate_cells(cells: List[str]) -> Tuple[str, List[int]]:
    """Joins cells with a blank-line separator; returns the combined
    source plus each cell's 1-based starting line in that source."""
    combined_lines: List[str] = []
    cell_start_lines: List[int] = []
    for source in cells:
        cell_start_lines.append(len(combined_lines) + 1)
        combined_lines.extend(source.splitlines())
        combined_lines.append("")
    return "\n".join(combined_lines), cell_start_lines


def _cell_index_for_line(line: int, cell_start_lines: List[int]) -> int:
    cell_index = 1
    for i, start in enumerate(cell_start_lines, start=1):
        if start <= line:
            cell_index = i
        else:
            break
    return cell_index


def find_undefined_names(
    source: str, cell_start_lines: List[int]
) -> List[UndefinedNameIssue]:
    tree = ast.parse(source)
    checker = Checker(tree)
    return [
        UndefinedNameIssue(
            cell_index=_cell_index_for_line(message.lineno, cell_start_lines),
            line=message.lineno,
            message=str(message),
        )
        for message in checker.messages
        if isinstance(message, UndefinedName)
    ]


def check_notebook_undefined_names(notebook_path: Path) -> List[UndefinedNameIssue]:
    cells = extract_code_cells(notebook_path)
    source, cell_start_lines = concatenate_cells(cells)
    return find_undefined_names(source, cell_start_lines)
