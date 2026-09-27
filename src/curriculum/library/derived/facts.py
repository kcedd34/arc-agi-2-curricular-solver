"""Per-task facts the derived family prunes with (ADR 0107): the cells each
train pair changes, and the regions of each input under one region kind.
Regions come from the interpreter's own partitions, so a probe and the
verified program cannot disagree."""
from typing import Dict, List, NamedTuple, Optional, Set, Tuple

from src.curriculum.grid import Grid, grid_dims
from src.curriculum.library.derived.lowering import partition_kind
from src.curriculum.library.derived.model import RegionSpec
from src.curriculum.library.objects._task_cache import cached_for_task
from src.curriculum.loader import Task
from src.curriculum.spec._region_value import RegionValue
from src.curriculum.spec.interpreter import _partition_grid

Cell = Tuple[int, int]


class PairChange(NamedTuple):
    cells: Set[Cell]
    new_colors: Set[int]  # output colours at the changed cells


def pair_change(input_grid: Grid, output_grid: Grid) -> PairChange:
    rows, cols = grid_dims(input_grid)
    cells = {(r, c) for r in range(rows) for c in range(cols) if input_grid[r][c] != output_grid[r][c]}
    return PairChange(cells, {output_grid[r][c] for r, c in cells})


def task_changes(task: Task) -> List[PairChange]:
    return cached_for_task(task, "derived_changes", lambda: [pair_change(p.input, p.output) for p in task.train])


def _regions(grid: Grid, spec: RegionSpec) -> Optional[List[RegionValue]]:
    try:
        return _partition_grid(grid, partition_kind(spec))
    except (ValueError, KeyError):
        return None


def train_regions(task: Task, spec: RegionSpec) -> Optional[List[List[RegionValue]]]:
    """Regions of every train input, or None when some input has none."""
    cache: Dict = cached_for_task(task, "derived_regions", dict)
    if spec not in cache:
        per_pair = [_regions(pair.input, spec) for pair in task.train]
        cache[spec] = None if any(not regions for regions in per_pair) else per_pair
    return cache[spec]


def bbox_cells(region: RegionValue) -> Set[Cell]:
    return {
        (region.row0 + r, region.col0 + c) for r in range(region.rows) for c in range(region.cols)
    }
