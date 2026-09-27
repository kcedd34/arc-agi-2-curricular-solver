"""Connected-component utilities shared by the ADR 0045 heuristic
diagnostics (`object_heuristics.py`: same-color components;
`symmetry_heuristics.py`: mismatch regions against a symmetry
transform). A minimal utility, not a general segmentation engine - it
exists to support cheap heuristic tests before committing to a full
object-level primitive build (ADR 0041 item 4).
"""
from typing import List, NamedTuple, Tuple

from src.utils.grid_types import Grid


class Component(NamedTuple):
    color: int
    cells: Tuple[Tuple[int, int], ...]


def _neighbors(r: int, c: int, connectivity: int) -> List[Tuple[int, int]]:
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if connectivity == 8:
        deltas += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    return [(r + dr, c + dc) for dr, dc in deltas]


def connected_regions(mask: List[List[bool]], connectivity: int = 4) -> List[List[Tuple[int, int]]]:
    """Groups True cells in a boolean mask into 4- or 8-connected regions."""
    height, width = len(mask), len(mask[0])
    visited = [[False] * width for _ in range(height)]
    regions = []
    for start_r in range(height):
        for start_c in range(width):
            if not mask[start_r][start_c] or visited[start_r][start_c]:
                continue
            stack = [(start_r, start_c)]
            visited[start_r][start_c] = True
            region = []
            while stack:
                r, c = stack.pop()
                region.append((r, c))
                for nr, nc in _neighbors(r, c, connectivity):
                    if 0 <= nr < height and 0 <= nc < width and mask[nr][nc] and not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))
            regions.append(region)
    return regions


def find_color_components(grid: Grid, connectivity: int, background: int) -> List[Component]:
    """Same-color connected components, excluding the background color."""
    height, width = len(grid), len(grid[0])
    colors = {cell for row in grid for cell in row} - {background}
    components = []
    for color in colors:
        mask = [[grid[r][c] == color for c in range(width)] for r in range(height)]
        for region in connected_regions(mask, connectivity):
            components.append(Component(color=color, cells=tuple(region)))
    return components


def bounding_box(cells) -> Tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def crop_to_bbox(grid: Grid, bbox: Tuple[int, int, int, int]) -> Grid:
    r0, c0, r1, c1 = bbox
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
