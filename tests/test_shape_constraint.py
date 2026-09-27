from src.solvers.neural.shape_constraint import force_grid_shape


def test_noop_when_shape_already_matches():
    grid = [[1, 2], [3, 4]]
    assert force_grid_shape(grid, 2, 2) == [[1, 2], [3, 4]]


def test_truncates_extra_rows():
    grid = [[1, 2], [3, 4], [5, 6], [7, 8]]
    assert force_grid_shape(grid, 2, 2) == [[1, 2], [3, 4]]


def test_pads_missing_rows_by_repeating_the_last_row():
    grid = [[1, 2], [3, 4]]
    assert force_grid_shape(grid, 4, 2) == [[1, 2], [3, 4], [3, 4], [3, 4]]


def test_truncates_extra_columns():
    grid = [[1, 2, 3], [4, 5, 6]]
    assert force_grid_shape(grid, 2, 2) == [[1, 2], [4, 5]]


def test_pads_missing_columns_by_repeating_the_last_value():
    grid = [[1, 2], [3, 4]]
    assert force_grid_shape(grid, 2, 4) == [[1, 2, 2, 2], [3, 4, 4, 4]]


def test_handles_an_empty_grid():
    assert force_grid_shape([], 2, 3) == [[0, 0, 0], [0, 0, 0]]


def test_combined_row_and_column_adjustment():
    grid = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    assert force_grid_shape(grid, 2, 2) == [[1, 2], [4, 5]]
