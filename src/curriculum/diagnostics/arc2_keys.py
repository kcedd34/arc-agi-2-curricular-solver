"""Per-cell context keys for the arc2_only diagnostic (ADR 0095).

Each key maps a cell of an input grid to a hashable description of its
context. A same-shape task is "explained by key K" when the output color
of every cell is a function of K(cell) alone (checked leave-one-pair-out
in `arc2_predictor`). Train pairs only (RN-CUR-03/05).
"""
from collections import Counter
from typing import Callable, Dict, Tuple

from src.curriculum.grid import Grid
from src.curriculum.perception.objects import infer_background, segment_objects

Cell = Tuple[int, int]
KeyMap = Dict[Cell, Tuple]


def _dims(grid: Grid) -> Cell:
    return len(grid), len(grid[0])


def key_color(grid: Grid) -> KeyMap:
    rows, cols = _dims(grid)
    return {(r, c): (grid[r][c],) for r in range(rows) for c in range(cols)}


def _object_map(grid: Grid) -> Dict[Cell, object]:
    background = infer_background(grid)
    owner = {}
    for obj in segment_objects(grid, background, 4, True):
        for cell in obj.cells:
            owner[cell] = obj
    return owner


def key_object_size(grid: Grid) -> KeyMap:
    owner = _object_map(grid)
    return {cell: (grid[cell[0]][cell[1]], owner[cell].size if cell in owner else 0) for cell in _all(grid)}


def key_object_rank(grid: Grid) -> KeyMap:
    owner = _object_map(grid)
    sizes = sorted({o.size for o in owner.values()})

    def rank(cell: Cell) -> int:
        if cell not in owner:
            return -1
        size = owner[cell].size
        return 0 if size == sizes[-1] else (1 if size == sizes[0] else 2)

    return {cell: (grid[cell[0]][cell[1]], rank(cell)) for cell in _all(grid)}


def key_border(grid: Grid) -> KeyMap:
    rows, cols = _dims(grid)
    owner = _object_map(grid)
    return {
        cell: (grid[cell[0]][cell[1]], cell in owner and owner[cell].touches_border(rows, cols))
        for cell in _all(grid)
    }


def key_neighbors(grid: Grid) -> KeyMap:
    rows, cols = _dims(grid)
    out = {}
    for r, c in _all(grid):
        around = frozenset(
            grid[r + dr][c + dc]
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if (dr or dc) and 0 <= r + dr < rows and 0 <= c + dc < cols
        )
        out[(r, c)] = (grid[r][c], around)
    return out


def _all(grid: Grid):
    rows, cols = _dims(grid)
    return [(r, c) for r in range(rows) for c in range(cols)]


def _objects8(grid: Grid):
    return segment_objects(grid, infer_background(grid), 8, True)


def _ordinal_key(grid: Grid, descending: bool) -> KeyMap:
    objects = _objects8(grid)
    sizes = sorted({o.size for o in objects}, reverse=descending)
    owner = {cell: sizes.index(o.size) for o in objects for cell in o.cells}
    return {cell: (grid[cell[0]][cell[1]], owner.get(cell, -1)) for cell in _all(grid)}


def key_size_ordinal_desc(grid: Grid) -> KeyMap:
    return _ordinal_key(grid, True)


def key_size_ordinal_asc(grid: Grid) -> KeyMap:
    return _ordinal_key(grid, False)


def key_color_frequency_rank(grid: Grid) -> KeyMap:
    counts = Counter(v for row in grid for v in row)
    order = sorted(set(counts.values()), reverse=True)
    return {cell: (grid[cell[0]][cell[1]], order.index(counts[grid[cell[0]][cell[1]]])) for cell in _all(grid)}


def _line_kind(cells) -> str:
    rows, cols = {r for r, _ in cells}, {c for _, c in cells}
    if len(cells) < 2:
        return "P"
    if len(rows) == 1:
        return "H"
    if len(cols) == 1:
        return "V"
    if len({r - c for r, c in cells}) == 1:
        return "D"
    return "A" if len({r + c for r, c in cells}) == 1 else "O"


def key_line_kind(grid: Grid) -> KeyMap:
    kinds = {cell: _line_kind(o.cells) for o in _objects8(grid) for cell in o.cells}
    return {cell: (grid[cell[0]][cell[1]], kinds.get(cell, "-")) for cell in _all(grid)}


def _cell_at(grid: Grid, r: int, c: int) -> int:
    inside = 0 <= r < len(grid) and 0 <= c < len(grid[0])
    return grid[r][c] if inside else -1


def key_window3(grid: Grid) -> KeyMap:
    return {
        (r, c): tuple(_cell_at(grid, r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1))
        for r, c in _all(grid)
    }


def _first_seen(grid: Grid, r: int, c: int, dr: int, dc: int, background: int) -> int:
    r, c = r + dr, c + dc
    while 0 <= r < len(grid) and 0 <= c < len(grid[0]):
        if grid[r][c] != background:
            return grid[r][c]
        r, c = r + dr, c + dc
    return -1


def _ray_key(grid: Grid, directions) -> KeyMap:
    background = infer_background(grid)
    return {
        (r, c): (grid[r][c],) + tuple(_first_seen(grid, r, c, dr, dc, background) for dr, dc in directions)
        for r, c in _all(grid)
    }


def key_rays4(grid: Grid) -> KeyMap:
    return _ray_key(grid, ((-1, 0), (1, 0), (0, -1), (0, 1)))


def key_rays8(grid: Grid) -> KeyMap:
    return _ray_key(grid, tuple((a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b))


KEYS: Dict[str, Callable[[Grid], KeyMap]] = {
    "cor": key_color,
    "cor+tamanho_do_objeto": key_object_size,
    "cor+posto_do_objeto": key_object_rank,
    "cor+toca_borda": key_border,
    "cor+vizinhanca": key_neighbors,
    "cor+posto_tamanho_desc": key_size_ordinal_desc,
    "cor+posto_tamanho_asc": key_size_ordinal_asc,
    "cor+posto_frequencia_da_cor": key_color_frequency_rank,
    "cor+tipo_de_linha": key_line_kind,
    "janela_3x3": key_window3,
    "cor+raios_4dir": key_rays4,
    "cor+raios_8dir": key_rays8,
}
