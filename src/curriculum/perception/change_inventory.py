"""Change inventory: per-demonstration-pair structural facts, aggregated
per task into hints true across ALL train pairs (object pack, Section
3.1, ADR 0069/RN-CUR-36).

Used by `search/pruning.py` (Phase 6) to hard-prune layouts/actions the
demonstrations already rule out, before enumeration. Reads only train
pairs, never a test output (RN-CUR-03/05): `PairInventory` is built from
one `TrainPair`, and `TaskInventory` aggregates only over `task.train`.
"""
from dataclasses import dataclass
from fractions import Fraction
from typing import FrozenSet, List, Optional, Tuple

from src.curriculum.grid import Grid, grid_dims
from src.curriculum.loader import Task, TrainPair
from src.curriculum.perception.objects import segment_objects

FEW_CELLS_CHANGE_THRESHOLD = 0.2

ShapeRatio = Tuple[Fraction, Fraction]


@dataclass(frozen=True)
class PairInventory:
    in_shape: Tuple[int, int]
    out_shape: Tuple[int, int]
    in_palette: FrozenSet[int]
    out_palette: FrozenSet[int]
    added_colors: FrozenSet[int]
    removed_colors: FrozenSet[int]
    changed_cells: Optional[int]
    total_cells: Optional[int]
    shape_ratio: ShapeRatio
    in_object_count: int
    out_object_count: int


def _palette(grid: Grid) -> FrozenSet[int]:
    return frozenset(cell for row in grid for cell in row)


def _changed_cell_count(input_grid: Grid, output_grid: Grid) -> Optional[int]:
    """None when shapes differ, since cell-by-cell comparison is
    undefined in that case."""
    if grid_dims(input_grid) != grid_dims(output_grid):
        return None
    return sum(
        1
        for in_row, out_row in zip(input_grid, output_grid)
        for a, b in zip(in_row, out_row)
        if a != b
    )


def _shape_ratio(in_shape: Tuple[int, int], out_shape: Tuple[int, int]) -> ShapeRatio:
    in_rows, in_cols = in_shape
    out_rows, out_cols = out_shape
    return (Fraction(out_rows, in_rows), Fraction(out_cols, in_cols))


def build_pair_inventory(pair: TrainPair) -> PairInventory:
    in_shape = grid_dims(pair.input)
    out_shape = grid_dims(pair.output)
    in_palette = _palette(pair.input)
    out_palette = _palette(pair.output)
    changed = _changed_cell_count(pair.input, pair.output)
    total = in_shape[0] * in_shape[1] if changed is not None else None
    return PairInventory(
        in_shape=in_shape,
        out_shape=out_shape,
        in_palette=in_palette,
        out_palette=out_palette,
        added_colors=out_palette - in_palette,
        removed_colors=in_palette - out_palette,
        changed_cells=changed,
        total_cells=total,
        shape_ratio=_shape_ratio(in_shape, out_shape),
        in_object_count=len(segment_objects(pair.input)),
        out_object_count=len(segment_objects(pair.output)),
    )


@dataclass(frozen=True)
class TaskInventory:
    same_shape: bool
    few_cells_change: bool
    constant_shape_ratio: bool
    constant_out_shape: bool
    shape_depends_on_content: bool
    no_new_colors: bool
    new_color_always_added: bool
    object_count_preserved: bool


def _all_same_shape(pairs: List[PairInventory]) -> bool:
    return all(p.in_shape == p.out_shape for p in pairs)


def _all_few_cells_change(pairs: List[PairInventory], same_shape: bool) -> bool:
    if not same_shape:
        return False
    for p in pairs:
        if not p.total_cells:
            return False
        if p.changed_cells / p.total_cells > FEW_CELLS_CHANGE_THRESHOLD:
            return False
    return True


def _all_constant_shape_ratio(pairs: List[PairInventory]) -> bool:
    first = pairs[0].shape_ratio
    return all(p.shape_ratio == first for p in pairs)


def _all_constant_out_shape(pairs: List[PairInventory]) -> bool:
    first = pairs[0].out_shape
    return all(p.out_shape == first for p in pairs)


def _all_no_new_colors(pairs: List[PairInventory]) -> bool:
    return all(not p.added_colors for p in pairs)


def _new_color_always_added(pairs: List[PairInventory]) -> bool:
    common = None
    for p in pairs:
        if not p.added_colors:
            return False
        common = p.added_colors if common is None else (common & p.added_colors)
    return bool(common)


def _all_object_count_preserved(pairs: List[PairInventory]) -> bool:
    return all(p.in_object_count == p.out_object_count for p in pairs)


def build_task_inventory(task: Task) -> TaskInventory:
    """Aggregate `PairInventory` facts across every train pair, keeping
    only facts true across ALL pairs (object pack, Section 3.1)."""
    pairs = [build_pair_inventory(p) for p in task.train]
    same_shape = _all_same_shape(pairs)
    constant_shape_ratio = (not same_shape) and _all_constant_shape_ratio(pairs)
    constant_out_shape = _all_constant_out_shape(pairs)
    shape_depends_on_content = not (same_shape or constant_shape_ratio or constant_out_shape)
    return TaskInventory(
        same_shape=same_shape,
        few_cells_change=_all_few_cells_change(pairs, same_shape),
        constant_shape_ratio=constant_shape_ratio,
        constant_out_shape=constant_out_shape,
        shape_depends_on_content=shape_depends_on_content,
        no_new_colors=_all_no_new_colors(pairs),
        new_color_always_added=_new_color_always_added(pairs),
        object_count_preserved=_all_object_count_preserved(pairs),
    )
