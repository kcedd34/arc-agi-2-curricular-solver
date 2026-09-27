from src.utils.grid_ops import (
    GEOMETRIC_TRANSFORMS,
    anti_transpose,
    identity,
    rotate90,
    rotate180,
    rotate270,
)


def test_geometric_transforms_has_all_eight_dihedral_elements():
    assert len(GEOMETRIC_TRANSFORMS) == 8


def test_anti_transpose_reflects_across_the_anti_diagonal():
    grid = [[1, 2], [3, 4]]
    assert anti_transpose(grid) == [[4, 2], [3, 1]]


def test_anti_transpose_is_its_own_inverse():
    grid = [[1, 2, 3], [4, 5, 6]]
    assert anti_transpose(anti_transpose(grid)) == grid


def test_four_rotations_return_to_identity():
    grid = [[1, 2, 3], [4, 5, 6]]
    assert rotate90(rotate90(rotate90(rotate90(grid)))) == identity(grid)
    assert rotate180(rotate180(grid)) == identity(grid)


def test_rotate270_is_the_inverse_of_rotate90():
    grid = [[1, 2, 3], [4, 5, 6]]
    assert rotate270(rotate90(grid)) == identity(grid)


def test_all_eight_transforms_are_distinct_on_an_asymmetric_grid():
    grid = [[1, 2], [3, 4]]
    results = [tuple(tuple(row) for row in transform(grid)) for transform in GEOMETRIC_TRANSFORMS]
    assert len(set(results)) == 8
