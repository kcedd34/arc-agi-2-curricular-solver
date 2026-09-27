"""Cheap symmetry-break-and-repair heuristic, tested against train pairs
only, before committing to a full symmetry-repair primitive build (ADR
0041 item 5). See ADR 0045.

For each of 3 symmetry kinds (horizontal mirror, vertical mirror, a
180-degree rotation): compare the input grid to its transformed self,
cell by cell. Since each of these transforms is an involution, a
genuine one-sided anomaly always shows up as mismatches on BOTH sides
(the damaged cell differs from its mirror partner, and the mirror
partner differs from the damaged cell right back) - so the mismatch
mask splits into at most 2 connected regions (4-connected), each the
mirror image of the other in position. Four candidate output forms are
tested per symmetry kind (2 regions x 2 read sources):
- as_found: the region's own bounding box, cropped straight from the
  input (whatever is actually there).
- repaired: the same bounding box, but reading cell values from the
  transformed grid instead (what the symmetric pattern says should be
  there).

Which region is the "real" anomaly and which is its clean counterpart
is not decided upfront - both region indices and both forms are tried,
and only the combination(s) that reproduce every train pair survive.
A grid with zero mismatches (already perfectly symmetric) or mismatches
split across more than 2 disconnected regions produces no candidate for
that symmetry kind on that pair - deliberately narrow, this is a
heuristic diagnostic, not a general symmetry-repair engine.

A (symmetry kind, region index, form) combination only counts as a
task-level candidate if it reproduces 100% of the task's train pairs;
`detect_symmetry_heuristics` pools all surviving combinations, the ADR
0038 ambiguity bar is the caller's job, same as every other primitive
in this project.
"""
from typing import List, NamedTuple, Optional, Tuple

from src.solvers.connected_components import bounding_box, connected_regions, crop_to_bbox
from src.utils.grid_ops import flip_horizontal, flip_vertical, rotate180
from src.utils.grid_types import Grid
from src.utils.task_loader import Pair

_SYMMETRIES = {
    "mirror_horizontal": flip_horizontal,
    "mirror_vertical": flip_vertical,
    "rotate_180": rotate180,
}


class SymmetryHeuristic(NamedTuple):
    symmetry: str
    region_index: int  # 0 or 1, selects among up to 2 symmetric mismatch regions
    form: str  # "as_found" or "repaired"


def _anomaly_bboxes(grid: Grid, transform) -> List[Tuple[int, int, int, int]]:
    transformed = transform(grid)
    if len(transformed) != len(grid) or len(transformed[0]) != len(grid[0]):
        return []
    height, width = len(grid), len(grid[0])
    mask = [[grid[r][c] != transformed[r][c] for c in range(width)] for r in range(height)]
    regions = connected_regions(mask, connectivity=4)
    if len(regions) not in (1, 2):
        return []
    return [bounding_box(region) for region in regions]


def apply_symmetry_heuristic(heuristic: SymmetryHeuristic, grid: Grid) -> Optional[Grid]:
    transform = _SYMMETRIES[heuristic.symmetry]
    bboxes = _anomaly_bboxes(grid, transform)
    if heuristic.region_index >= len(bboxes):
        return None
    source = grid if heuristic.form == "as_found" else transform(grid)
    return crop_to_bbox(source, bboxes[heuristic.region_index])


def all_symmetry_heuristics() -> List[SymmetryHeuristic]:
    return [
        SymmetryHeuristic(symmetry, region_index, form)
        for symmetry in _SYMMETRIES
        for region_index in (0, 1)
        for form in ("as_found", "repaired")
    ]


def detect_symmetry_heuristics(pairs: List[Pair]) -> List[SymmetryHeuristic]:
    return [
        heuristic
        for heuristic in all_symmetry_heuristics()
        if all(apply_symmetry_heuristic(heuristic, p.input) == p.output for p in pairs)
    ]
