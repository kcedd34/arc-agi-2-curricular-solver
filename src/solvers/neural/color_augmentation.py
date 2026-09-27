"""Color-permutation augmentation for TTT training pairs.

Applied on top of the existing geometric augmentation
(src/utils/grid_ops.py), only to already-augmented train pairs, never the
test input (the caller, ttt_trainer.py, only expands the training set).
Color 0 is kept fixed on the assumption that it usually encodes grid
background rather than a task-specific symbol; only the non-zero colors
actually present in a pair are permuted, and the same permutation is
applied to both the input and output side of that pair, so the
transformation the pair demonstrates is preserved. See
docs/decisions/0027-color-augmentation-sanity.md.
"""
import random
from typing import Dict, List

from src.utils.grid_types import Grid
from src.utils.task_loader import Pair


def colors_present(pair: Pair) -> List[int]:
    """Non-zero colors appearing in either side of the pair, sorted for a
    deterministic permutation order."""
    values = {cell for row in pair.input for cell in row}
    values |= {cell for row in pair.output for cell in row}
    values.discard(0)
    return sorted(values)


def _random_permutation(colors: List[int], rng: random.Random) -> Dict[int, int]:
    shuffled = colors[:]
    rng.shuffle(shuffled)
    return dict(zip(colors, shuffled))


def apply_color_mapping(grid: Grid, mapping: Dict[int, int]) -> Grid:
    return [[mapping.get(cell, cell) for cell in row] for row in grid]


def generate_color_variant(pair: Pair, rng: random.Random) -> Pair:
    mapping = _random_permutation(colors_present(pair), rng)
    return Pair(apply_color_mapping(pair.input, mapping), apply_color_mapping(pair.output, mapping))


def expand_pairs_with_color_variants(pairs: List[Pair], num_variants: int, seed: int) -> List[Pair]:
    """For each pair, keeps the original and appends num_variants
    color-shuffled copies. Deterministic for a given seed and pair order,
    so a training run is reproducible across re-runs."""
    rng = random.Random(seed)
    expanded: List[Pair] = []
    for pair in pairs:
        expanded.append(pair)
        expanded.extend(generate_color_variant(pair, rng) for _ in range(num_variants))
    return expanded
