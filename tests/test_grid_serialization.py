from src.solvers.neural.grid_serialization import grid_to_text, text_to_grid


def test_round_trip_preserves_grid():
    grid = [[1, 2, 3], [4, 0, 9]]
    assert text_to_grid(grid_to_text(grid)) == grid


def test_text_to_grid_rejects_non_digit_characters():
    assert text_to_grid("12\n3a") is None


def test_text_to_grid_rejects_ragged_rows():
    assert text_to_grid("12\n345") is None


def test_text_to_grid_rejects_empty_text():
    assert text_to_grid("   \n  ") is None


def test_grid_to_text_single_cell():
    assert grid_to_text([[5]]) == "5"
