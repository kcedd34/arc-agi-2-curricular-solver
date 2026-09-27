from src.curriculum.grid import (
    deep_copy_grid,
    empty_grid,
    grid_dims,
    grids_equal,
    is_valid_grid,
)


def test_grid_dims_rectangular():
    assert grid_dims([[1, 2], [3, 4], [5, 6]]) == (3, 2)


def test_grid_dims_ragged_raises():
    try:
        grid_dims([[1, 2], [3]])
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_is_valid_grid_true():
    assert is_valid_grid([[0, 9], [1, 8]])


def test_is_valid_grid_false_out_of_range():
    assert not is_valid_grid([[0, 10]])


def test_is_valid_grid_false_ragged():
    assert not is_valid_grid([[1, 2], [3]])


def test_is_valid_grid_false_empty():
    assert not is_valid_grid([])
    assert not is_valid_grid([[]])


def test_grids_equal():
    assert grids_equal([[1, 2]], [[1, 2]])
    assert not grids_equal([[1, 2]], [[1, 3]])
    assert not grids_equal([[1, 2]], [[1, 2], [3, 4]])


def test_deep_copy_grid_is_independent():
    original = [[1, 2], [3, 4]]
    copy = deep_copy_grid(original)
    copy[0][0] = 9
    assert original[0][0] == 1


def test_empty_grid():
    grid = empty_grid(2, 3, fill=5)
    assert grid == [[5, 5, 5], [5, 5, 5]]
