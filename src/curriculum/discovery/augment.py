"""Task augmentations for the robustness filter (ADR 0110): the seven non
identity symmetries of the square and a deterministic permutation of the
non-background colours. A property that only holds in one orientation, or for
one absolute colour, is not a discovered rule."""
from typing import Callable, Dict, List

from src.curriculum.grid import Grid
from src.curriculum.loader import Task, TrainPair


def _rot90(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid[::-1])]


def _rot180(grid: Grid) -> Grid:
    return [row[::-1] for row in grid[::-1]]


def _rot270(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid)][::-1]


def _flip_h(grid: Grid) -> Grid:
    return [row[::-1] for row in grid]


def _flip_v(grid: Grid) -> Grid:
    return [row[:] for row in grid[::-1]]


def _transpose(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid)]


def _anti_transpose(grid: Grid) -> Grid:
    return _rot180(_transpose(grid))


GEOMETRIC: Dict[str, Callable[[Grid], Grid]] = {
    "rot90": _rot90,
    "rot180": _rot180,
    "rot270": _rot270,
    "flip_h": _flip_h,
    "flip_v": _flip_v,
    "transpose": _transpose,
    "anti_transpose": _anti_transpose,
}


def transformed_task(task: Task, fn: Callable[[Grid], Grid]) -> Task:
    train = [TrainPair(fn(p.input), fn(p.output)) for p in task.train]
    return Task(task.task_id, train, [])


def color_permutation(task: Task, background: int) -> Dict[int, int]:
    """Cyclic shift of the non-background colours the task uses (identity when
    fewer than two)."""
    colors = sorted({v for p in task.train for g in (p.input, p.output) for row in g for v in row} - {background})
    if len(colors) < 2:
        return {}
    return {c: colors[(i + 1) % len(colors)] for i, c in enumerate(colors)}


def permuted_task(task: Task, mapping: Dict[int, int]) -> Task:
    def apply(grid: Grid) -> Grid:
        return [[mapping.get(v, v) for v in row] for row in grid]

    return transformed_task(task, apply)


def augmentation_names(with_colors: bool) -> List[str]:
    return list(GEOMETRIC) + (["colors"] if with_colors else [])
