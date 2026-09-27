"""Grid <-> text serialization used to prompt and parse the neural solver."""
from typing import List, Optional

from src.utils.grid_types import Grid


def grid_to_rows(grid: Grid) -> List[str]:
    return ["".join(str(cell) for cell in row) for row in grid]


def grid_to_text(grid: Grid) -> str:
    return "\n".join(grid_to_rows(grid))


def _parse_row(line: str) -> Optional[List[int]]:
    if not line or not line.isdigit():
        return None
    return [int(char) for char in line]


def _is_rectangular(rows: List[List[int]]) -> bool:
    return len(rows) > 0 and len({len(row) for row in rows}) == 1


def text_to_grid(text: str) -> Optional[Grid]:
    lines = [line for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return None
    rows = [_parse_row(line) for line in lines]
    if any(row is None for row in rows):
        return None
    if not _is_rectangular(rows):
        return None
    return rows
