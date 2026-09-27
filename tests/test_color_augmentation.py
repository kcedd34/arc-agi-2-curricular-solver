import random

from src.solvers.neural.color_augmentation import (
    apply_color_mapping,
    colors_present,
    expand_pairs_with_color_variants,
    generate_color_variant,
)
from src.utils.task_loader import Pair


def test_colors_present_excludes_zero_and_is_sorted():
    pair = Pair(input=[[0, 2, 1]], output=[[3, 0, 1]])
    assert colors_present(pair) == [1, 2, 3]


def test_colors_present_handles_an_all_zero_grid():
    pair = Pair(input=[[0, 0]], output=[[0, 0]])
    assert colors_present(pair) == []


def test_apply_color_mapping_keeps_background_fixed():
    grid = [[0, 1], [2, 0]]
    mapping = {1: 2, 2: 1}
    assert apply_color_mapping(grid, mapping) == [[0, 2], [1, 0]]


def test_apply_color_mapping_passes_through_unmapped_values():
    grid = [[5]]
    assert apply_color_mapping(grid, {}) == [[5]]


def test_generate_color_variant_applies_the_same_mapping_to_both_sides():
    pair = Pair(input=[[1, 2]], output=[[2, 1]])
    variant = generate_color_variant(pair, random.Random(0))
    # whatever mapping was drawn, the input/output relationship (each row
    # reversed) must survive, since both sides go through the same mapping
    assert variant.input == [row[::-1] for row in variant.output]


def test_generate_color_variant_preserves_shape():
    pair = Pair(input=[[1, 2], [3, 4]], output=[[4, 3], [2, 1]])
    variant = generate_color_variant(pair, random.Random(1))
    assert len(variant.input) == 2 and len(variant.input[0]) == 2
    assert len(variant.output) == 2 and len(variant.output[0]) == 2


def test_generate_color_variant_only_uses_colors_from_the_original_pair():
    pair = Pair(input=[[1, 2, 3]], output=[[3, 2, 1]])
    variant = generate_color_variant(pair, random.Random(2))
    original_colors = set(colors_present(pair))
    variant_colors = {cell for row in variant.input + variant.output for cell in row} - {0}
    assert variant_colors <= original_colors


def test_generate_color_variant_never_remaps_background():
    pair = Pair(input=[[0, 1, 2]], output=[[0, 2, 1]])
    variant = generate_color_variant(pair, random.Random(5))
    assert variant.input[0][0] == 0
    assert variant.output[0][0] == 0


def test_expand_pairs_with_color_variants_counts_originals_plus_variants():
    pairs = [Pair(input=[[1, 2]], output=[[2, 1]]), Pair(input=[[3]], output=[[3]])]
    expanded = expand_pairs_with_color_variants(pairs, num_variants=2, seed=42)
    assert len(expanded) == len(pairs) * 3


def test_expand_pairs_with_color_variants_keeps_the_original_pairs():
    pairs = [Pair(input=[[1, 2]], output=[[2, 1]])]
    expanded = expand_pairs_with_color_variants(pairs, num_variants=2, seed=42)
    assert expanded[0] == pairs[0]


def test_expand_pairs_with_color_variants_is_deterministic():
    pairs = [Pair(input=[[1, 2, 3]], output=[[3, 1, 2]])]
    first = expand_pairs_with_color_variants(pairs, num_variants=3, seed=7)
    second = expand_pairs_with_color_variants(pairs, num_variants=3, seed=7)
    assert first == second


def test_expand_pairs_with_color_variants_with_zero_variants_is_a_noop():
    pairs = [Pair(input=[[1, 2]], output=[[2, 1]])]
    expanded = expand_pairs_with_color_variants(pairs, num_variants=0, seed=42)
    assert expanded == pairs
