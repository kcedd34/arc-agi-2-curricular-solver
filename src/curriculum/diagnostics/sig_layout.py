"""Output-layout signatures (ADR 0093). Train pairs only (RN-CUR-03/05):
scaling, tiling, sub-grid overlay, crop and scalar outputs."""
from typing import Dict, List, Optional

Grid = List[List[int]]


def _dims(g: Grid):
    return len(g), len(g[0])


def _scale_factor(pair: Dict) -> Optional[tuple]:
    (ih, iw), (oh, ow) = _dims(pair["input"]), _dims(pair["output"])
    if oh % ih or ow % iw or (oh, ow) == (ih, iw):
        return None
    return oh // ih, ow // iw


def _is_solid_scaling(pair: Dict, factor: tuple) -> bool:
    kr, kc = factor
    a, b = pair["input"], pair["output"]
    return all(b[r][c] == a[r // kr][c // kc] for r in range(len(b)) for c in range(len(b[0])))


def enlargement_family(train: List[Dict]) -> Optional[str]:
    """"ampliacao_por_bloco_solido" (each cell becomes a solid block) or
    "grade_de_blocos" (other integer multiple), else None."""
    factors = [_scale_factor(p) for p in train]
    if None in factors:
        return None
    if all(_is_solid_scaling(p, f) for p, f in zip(train, factors)):
        return "ampliacao_por_bloco_solido"
    return "grade_de_blocos"


def _axis_starts(total: int, part: int) -> Optional[List[int]]:
    """Start offsets of equal parts along one axis, with or without a
    one-cell divider between them; None if the axis does not split."""
    for step in (part, part + 1):
        count = (total + (step - part)) // step
        if count >= 1 and count * step - (step - part) == total:
            return [i * step for i in range(count)]
    return None


def _parts(grid: Grid, out_h: int, out_w: int) -> Optional[List[Grid]]:
    rows, cols = _axis_starts(len(grid), out_h), _axis_starts(len(grid[0]), out_w)
    if rows is None or cols is None or len(rows) * len(cols) < 2:
        return None
    return [[row[c : c + out_w] for row in grid[r : r + out_h]] for r in rows for c in cols]


def _overlay_table(train: List[Dict]) -> Optional[Dict]:
    """Maps each tuple of part-cell values to the output value; None when
    some pair does not split or two cells disagree."""
    table: Dict = {}
    for pair in train:
        out = pair["output"]
        parts = _parts(pair["input"], len(out), len(out[0]))
        if parts is None or all(p == parts[0] for p in parts):
            return None
        for r in range(len(out)):
            for c in range(len(out[0])):
                if table.setdefault(tuple(p[r][c] for p in parts), out[r][c]) != out[r][c]:
                    return None
    return table


def subgrid_overlay_family(train: List[Dict]) -> Optional[str]:
    """Input splits into equal (optionally divider-separated) parts and each
    output cell is a fixed function of the parts' cells at that position."""
    return "sobreposicao_booleana_subgrids" if _overlay_table(train) is not None else None


def _contains_subgrid(big: Grid, small: Grid) -> bool:
    (bh, bw), (sh, sw) = _dims(big), _dims(small)
    return any(
        all(big[r + i][c : c + sw] == small[i] for i in range(sh))
        for r in range(bh - sh + 1)
        for c in range(bw - sw + 1)
    )


def is_crop_family(train: List[Dict]) -> bool:
    return all(_contains_subgrid(p["input"], p["output"]) for p in train)


def is_scalar_output(train: List[Dict]) -> bool:
    return all(_dims(p["output"]) == (1, 1) for p in train)
