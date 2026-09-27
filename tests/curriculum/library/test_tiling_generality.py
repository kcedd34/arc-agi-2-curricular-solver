"""Item 3.3 (RN-CUR-30 acceptance review) generality tests for block_tile_by_background.

None of these grids are 007bbfb7's own 3x3 geometry, colors, or scale: they
exist to prove `build_block_tile_by_background` is a genuine RxC block-tile
rule, not a primitive that only happens to reproduce one task. Per
`_regions.py`'s `_resolve_block_at`, each emitted block's size is exactly
`(scale_rows, scale_cols)` (`out_rows // extent_rows`, `out_cols //
extent_cols`, where the partition extent is the input grid's own shape), and
`_exec_emit` requires a `Copy` source's shape to match its region's shape
exactly - so a full-grid-copy block tile is only satisfiable when
`scale_rows == rows_in` and `scale_cols == cols_in`. Every case below sets
the two scale factors to the input's own row/col count for that reason, the
same fractal-expansion shape 007bbfb7 itself uses, just at different sizes,
colors, and (for the 2x3 case) a non-square aspect ratio.
"""
from src.curriculum.library.primitives import tiling  # noqa: F401 (registers the primitive)
from src.curriculum.library.registry import REGISTRY
from src.curriculum.spec import interpreter


def _run(input_grid, background):
    rows_in = len(input_grid)
    cols_in = len(input_grid[0])
    steps = REGISTRY.build(
        "block_tile_by_background",
        background=background,
        scale_rows=rows_in,
        scale_cols=cols_in,
    )
    return interpreter.run(steps, input_grid)


def _expected(input_grid, background):
    """Reference fractal-tile implementation, independent of the primitive under test."""
    rows_in = len(input_grid)
    cols_in = len(input_grid[0])
    out = [[background] * (cols_in * cols_in) for _ in range(rows_in * rows_in)]
    for r in range(rows_in):
        for c in range(cols_in):
            if input_grid[r][c] != background:
                for dr in range(rows_in):
                    for dc in range(cols_in):
                        out[r * rows_in + dr][c * cols_in + dc] = input_grid[dr][dc]
    return out


def test_2x2_grid_non_default_colors():
    input_grid = [[5, 0], [0, 5]]
    output_grid, _trace = _run(input_grid, background=0)
    assert output_grid == _expected(input_grid, background=0)
    assert len(output_grid) == 4 and len(output_grid[0]) == 4


def test_4x4_grid_non_default_background():
    input_grid = [
        [2, 2, 2, 8],
        [2, 8, 2, 2],
        [2, 2, 8, 2],
        [8, 2, 2, 2],
    ]
    output_grid, _trace = _run(input_grid, background=8)
    assert output_grid == _expected(input_grid, background=8)
    assert len(output_grid) == 16 and len(output_grid[0]) == 16


def test_2x3_non_square_grid():
    input_grid = [[4, 0, 4], [0, 4, 0]]
    output_grid, _trace = _run(input_grid, background=0)
    assert output_grid == _expected(input_grid, background=0)
    assert len(output_grid) == 4 and len(output_grid[0]) == 9


def test_3x2_non_square_grid_different_background_and_color():
    input_grid = [[1, 6], [6, 1], [1, 1]]
    output_grid, _trace = _run(input_grid, background=6)
    assert output_grid == _expected(input_grid, background=6)
    assert len(output_grid) == 9 and len(output_grid[0]) == 4
