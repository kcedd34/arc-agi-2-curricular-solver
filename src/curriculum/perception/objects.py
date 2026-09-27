"""Object perception: background inference, connected-component
segmentation, object representation, crop, and tie-safe selection
(object pack, Section 3.2, ADR 0069/RN-CUR-36).

This is one of two independent segmentation implementations required by
RN-CUR-14: the declarative trace interpreter's own vocabulary-v2
segmentation (`spec/_regions.py`) is written separately and never
imports this module. This module is the one used by search-side
perception (`change_inventory.py`, staging pieces' parameter inference).
"""
from collections import Counter, deque
from dataclasses import dataclass
from typing import FrozenSet, List, Optional, Tuple

from src.curriculum.grid import Grid, grid_dims

Cell = Tuple[int, int]

_CONNECTIVITY_4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CONNECTIVITY_8 = _CONNECTIVITY_4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))


@dataclass(frozen=True)
class ObjectInstance:
    cells: FrozenSet[Cell]
    colors: FrozenSet[int]
    top: int
    left: int
    bottom: int
    right: int

    @property
    def size(self) -> int:
        return len(self.cells)

    @property
    def height(self) -> int:
        return self.bottom - self.top + 1

    @property
    def width(self) -> int:
        return self.right - self.left + 1

    @property
    def color(self) -> Optional[int]:
        """The single color of this object, or None when multi-color."""
        if len(self.colors) == 1:
            return next(iter(self.colors))
        return None

    def touches_border(self, num_rows: int, num_cols: int) -> bool:
        return (
            self.top == 0
            or self.left == 0
            or self.bottom == num_rows - 1
            or self.right == num_cols - 1
        )


def infer_background(grid: Grid) -> int:
    """Most frequent color in the grid; ties broken by lowest color
    value (object pack, Section 3.2.1)."""
    counts = Counter(cell for row in grid for cell in row)
    best_color = None
    best_count = -1
    for color in sorted(counts):
        if counts[color] > best_count:
            best_color = color
            best_count = counts[color]
    return best_color


def _neighbors(cell: Cell, offsets: Tuple[Tuple[int, int], ...]) -> List[Cell]:
    row, col = cell
    return [(row + dr, col + dc) for dr, dc in offsets]


def _grow_component(
    grid: Grid,
    start: Cell,
    visited,
    background: int,
    offsets: Tuple[Tuple[int, int], ...],
    single_color: bool,
) -> FrozenSet[Cell]:
    num_rows, num_cols = grid_dims(grid)
    start_color = grid[start[0]][start[1]]
    queue = deque([start])
    visited.add(start)
    cells = [start]
    while queue:
        current = queue.popleft()
        for nb in _neighbors(current, offsets):
            nr, nc = nb
            if not (0 <= nr < num_rows and 0 <= nc < num_cols):
                continue
            if nb in visited:
                continue
            color = grid[nr][nc]
            if color == background:
                continue
            if single_color and color != start_color:
                continue
            visited.add(nb)
            queue.append(nb)
            cells.append(nb)
    return frozenset(cells)


def _build_object(grid: Grid, cells: FrozenSet[Cell]) -> ObjectInstance:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    colors = frozenset(grid[r][c] for r, c in cells)
    return ObjectInstance(
        cells=cells,
        colors=colors,
        top=min(rows),
        left=min(cols),
        bottom=max(rows),
        right=max(cols),
    )


def segment_objects(
    grid: Grid,
    background: Optional[int] = None,
    connectivity: int = 4,
    single_color: bool = True,
) -> List[ObjectInstance]:
    """Connected components of non-background cells, in reading order of
    each component's first (topmost, then leftmost) cell.

    `connectivity` is 4 or 8. `single_color` True separates components by
    color (a component never mixes colors); False groups any touching
    non-background cells regardless of color. Background defaults to
    `infer_background(grid)` when not given.
    """
    if connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    if background is None:
        background = infer_background(grid)
    offsets = _CONNECTIVITY_4 if connectivity == 4 else _CONNECTIVITY_8
    num_rows, num_cols = grid_dims(grid)
    visited = set()
    objects = []
    for row in range(num_rows):
        for col in range(num_cols):
            cell = (row, col)
            if cell in visited or grid[row][col] == background:
                continue
            cells = _grow_component(grid, cell, visited, background, offsets, single_color)
            objects.append(_build_object(grid, cells))
    return objects


def crop_to_bbox(grid: Grid, obj: ObjectInstance, fill: int) -> Grid:
    """Crop `grid` to `obj`'s bounding box; cells inside the box that are
    not part of `obj` are replaced with `fill`."""
    cropped = []
    for row in range(obj.top, obj.bottom + 1):
        new_row = []
        for col in range(obj.left, obj.right + 1):
            if (row, col) in obj.cells:
                new_row.append(grid[row][col])
            else:
                new_row.append(fill)
        cropped.append(new_row)
    return cropped


def select_largest(objects: List[ObjectInstance]) -> Optional[ObjectInstance]:
    return _select_by_extreme(objects, maximize=True)


def select_smallest(objects: List[ObjectInstance]) -> Optional[ObjectInstance]:
    return _select_by_extreme(objects, maximize=False)


def _select_by_extreme(
    objects: List[ObjectInstance], maximize: bool
) -> Optional[ObjectInstance]:
    """Never breaks a tie silently: more than one object at the extreme
    size returns None (object pack, Section 3.2.5)."""
    if not objects:
        return None
    target = max(o.size for o in objects) if maximize else min(o.size for o in objects)
    matches = [o for o in objects if o.size == target]
    return matches[0] if len(matches) == 1 else None


def select_unique_color(objects: List[ObjectInstance]) -> Optional[ObjectInstance]:
    """The single object whose (monochromatic) color no other object
    shares. None when zero or more than one object qualifies."""
    color_counts = Counter(o.color for o in objects if o.color is not None)
    unique = [o for o in objects if o.color is not None and color_counts[o.color] == 1]
    return unique[0] if len(unique) == 1 else None
