"""Region kinds the derived family walks, pruned by the task inventory
(ADR 0107). Segment kinds need a two-cell line in some train input."""
from typing import List

from src.curriculum.grid import grid_dims
from src.curriculum.library.derived.model import RegionSpec
from src.curriculum.library.objects.object_params import (
    background_candidates,
    connectivity_single_color_candidates,
    should_include_identity_canvas,
)
from src.curriculum.loader import Task


def has_two_cell_line(task: Task, background: int, axis: str) -> bool:
    """Some train input has a row (or column) with exactly two non-background cells."""
    for pair in task.train:
        grid = pair.input
        rows, cols = grid_dims(grid)
        lines = grid if axis == "row" else [[grid[r][c] for r in range(rows)] for c in range(cols)]
        if any(sum(1 for v in line if v != background) == 2 for line in lines):
            return True
    return False


def region_specs(task: Task) -> List[RegionSpec]:
    if not should_include_identity_canvas(task):
        return []
    specs = []
    for background in background_candidates(task):
        for axis, kind in (("row", "row_segments"), ("col", "col_segments")):
            if has_two_cell_line(task, background, axis):
                specs.append(RegionSpec(kind, 4, True, background))
        for connectivity, single_color in connectivity_single_color_candidates(task):
            specs.append(RegionSpec("objects", connectivity, single_color, background))
    return specs
