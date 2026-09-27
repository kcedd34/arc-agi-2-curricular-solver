"""Interpreter tests: independence (RN-CUR-14) and the ADR 0062 acceptance spec.

The `007bbfb7` step sequence below is transcribed verbatim from ADR 0062's
own "Worked example: 007bbfb7" section, which the ADR explicitly names as
this interpreter's acceptance test. `bg = 0` is an ADR-mandated constant
for this fixture only: it must never leak into vocabulary.py/interpreter.py
outside this test, since the real Stage-1 learner must infer background
color from demonstrations, not have it handed to it.
"""
import ast
from pathlib import Path

import pytest

from src.curriculum.loader import load_task
from src.curriculum.spec import interpreter, vocabulary as vocab

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def test_interpreter_independence():
    """RN-CUR-14: the trace interpreter must never import the primitive
    library, so a desk check never needs to read library code to trust a
    trace. Also never imports `perception/` (object pack Section 3.3): the
    interpreter's own object segmentation (`_partition_objects` in
    interpreter.py) is a second, independent implementation from
    `perception/objects.py::segment_objects`, compared only by the
    equivalence test below, never by sharing code. Checked statically
    (import graph), not just "not currently imported", so the guarantee
    survives future edits."""
    spec_dir = Path("src/curriculum/spec")
    forbidden = ("curriculum.library", "curriculum.perception")
    checked = 0
    for path in spec_dir.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module] if node.module else []
            else:
                continue
            for name in names:
                assert name is not None and not any(f in name for f in forbidden), (
                    f"{path}: forbidden import ({name!r}), violates RN-CUR-14"
                )
        checked += 1
    assert checked >= 5  # vocabulary, interpreter, _expressions, _regions, _region_value


def _block_at(row: vocab.Expr, col: vocab.Expr) -> vocab.BlockAt:
    return vocab.BlockAt(row=row, col=col)


def _build_007bbfb7_steps(bg: int) -> list:
    """ADR 0062's worked example for 007bbfb7, verbatim:

    1. bind g_in = input
    2. shape_out(g_in.rows * 3, g_in.cols * 3)
    3. partition(g_in, cells, result_name="in_cells")
    4. for_each cell in in_cells:
         test(is_background(cell, bg), result_name="cell_is_bg")
         branch(cell_is_bg):
           then: emit(block_at(cell.row, cell.col), fill(bg))
           else: emit(block_at(cell.row, cell.col), copy(g_in))
    5. compose(default_color=bg)
    """
    return [
        vocab.Bind(name="g_in", value=vocab.Ref("input")),
        vocab.ShapeOut(
            rows=vocab.BinOp("*", vocab.Attr(vocab.Ref("g_in"), "rows"), 3),
            cols=vocab.BinOp("*", vocab.Attr(vocab.Ref("g_in"), "cols"), 3),
        ),
        vocab.Partition(
            source=vocab.Ref("g_in"), kind=vocab.Cells(), result_name="in_cells"
        ),
        vocab.ForEach(
            list_ref=vocab.Ref("in_cells"),
            element_name="cell",
            body=[
                vocab.Test(
                    predicate=vocab.IsBackground(
                        value=vocab.Ref("cell"), background=bg
                    ),
                    result_name="cell_is_bg",
                ),
                vocab.Branch(
                    condition_name="cell_is_bg",
                    then_steps=[
                        vocab.Emit(
                            region=_block_at(
                                vocab.Attr(vocab.Ref("cell"), "row"),
                                vocab.Attr(vocab.Ref("cell"), "col"),
                            ),
                            source=vocab.Fill(color=bg),
                        ),
                    ],
                    else_steps=[
                        vocab.Emit(
                            region=_block_at(
                                vocab.Attr(vocab.Ref("cell"), "row"),
                                vocab.Attr(vocab.Ref("cell"), "col"),
                            ),
                            source=vocab.Copy(source=vocab.Ref("g_in")),
                        ),
                    ],
                ),
            ],
        ),
        vocab.Compose(default_color=bg),
    ]


def test_007bbfb7_acceptance_spec():
    """ADR 0062's own acceptance test: executing its worked example against
    007bbfb7's real train pairs must reproduce every training output
    exactly."""
    task = load_task(TRAINING_DIR / "007bbfb7.json")
    steps = _build_007bbfb7_steps(bg=0)
    for pair in task.train:
        output_grid, trace = interpreter.run(steps, pair.input)
        assert output_grid == pair.output
        assert trace[0]["op"] == "bind"
        assert trace[-1]["op"] == "compose"
        assert [entry["step"] for entry in trace] == list(range(1, len(trace) + 1))


def test_partition_grid_index_grid_generates_synthetic_regions():
    """IndexGrid (RN-CUR-31 exhaustion evidence,
    docs/curriculum/tasks/00576224.md) must generate rows * cols regions
    with row0/col0 spanning range(rows) x range(cols), independent of any
    real grid - _partition_grid is called with grid=None to prove this."""
    regions = interpreter._partition_grid(None, vocab.IndexGrid(rows=2, cols=3))
    assert [(r.row0, r.col0) for r in regions] == [
        (0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2),
    ]
    assert all((r.rows, r.cols) == (1, 1) for r in regions)


def test_partition_grid_objects_dispatches_single_color_flag():
    """`_partition_grid` must thread `kind.single_color` through to
    `_partition_objects` (object pack Section 3.3's
    `objects(connectivity, background, single_color)`): two touching
    cells of different colors form one component when single_color=False,
    two when single_color=True (default)."""
    grid = [[1, 2], [0, 0]]
    separated = interpreter._partition_grid(
        grid, vocab.Objects(connectivity=4, background=0)
    )
    assert len(separated) == 2

    merged = interpreter._partition_grid(
        grid, vocab.Objects(connectivity=4, background=0, single_color=False)
    )
    assert len(merged) == 1
    assert merged[0].cells == [[1, 2]]


def test_partition_objects_uses_none_for_non_member_bbox_cells():
    """A non-rectangular object's bounding box may contain cells that are
    not part of the object itself; those are None (sparse mask), never
    the literal background color (object pack Section 3.2's object
    representation)."""
    grid = [
        [5, 0],
        [5, 5],
    ]
    regions = interpreter._partition_objects(grid, connectivity=4, background=0)
    assert len(regions) == 1
    assert regions[0].cells == [[5, None], [5, 5]]


def test_index_grid_layout_tiles_independent_of_input_shape():
    """End-to-end: a 3x3 IndexGrid layout combined with the existing
    block_at/copy machinery must tile a 2x2 input into a 6x6 output, with
    the block count/extent coming from IndexGrid's own rows/cols, not from
    partitioning the 2x2 input (which Cells()/Blocks() could never yield 9
    regions from)."""
    steps = [
        vocab.Bind(name="g_in", value=vocab.Ref("input")),
        vocab.ShapeOut(rows=6, cols=6),
        vocab.Partition(
            source=vocab.Ref("g_in"),
            kind=vocab.IndexGrid(rows=3, cols=3),
            result_name="blocks",
        ),
        vocab.ForEach(
            list_ref=vocab.Ref("blocks"),
            element_name="block",
            body=[
                vocab.Emit(
                    region=_block_at(
                        vocab.Attr(vocab.Ref("block"), "row"),
                        vocab.Attr(vocab.Ref("block"), "col"),
                    ),
                    source=vocab.Copy(source=vocab.Ref("g_in")),
                ),
            ],
        ),
        vocab.Compose(default_color=0),
    ]
    output_grid, trace = interpreter.run(steps, [[7, 9], [4, 3]])
    assert output_grid == [
        [7, 9, 7, 9, 7, 9],
        [4, 3, 4, 3, 4, 3],
        [7, 9, 7, 9, 7, 9],
        [4, 3, 4, 3, 4, 3],
        [7, 9, 7, 9, 7, 9],
        [4, 3, 4, 3, 4, 3],
    ]
    partition_entry = next(entry for entry in trace if entry["op"] == "partition")
    assert partition_entry["value"] == 9


def test_seed_copies_source_into_output_grid():
    """ADR 0066: `Seed` pre-fills the canvas from a same-size source,
    before any selective overwrite."""
    steps = [
        vocab.Bind(name="g_in", value=vocab.Ref("input")),
        vocab.ShapeOut(rows=vocab.Attr(vocab.Ref("g_in"), "rows"), cols=vocab.Attr(vocab.Ref("g_in"), "cols")),
        vocab.Seed(source=vocab.Ref("g_in")),
        vocab.Compose(default_color=0),
    ]
    output_grid, trace = interpreter.run(steps, [[7, 9], [4, 3]])
    assert output_grid == [[7, 9], [4, 3]]
    assert any(entry["op"] == "seed" for entry in trace)


def test_seed_shape_mismatch_raises_interpreter_error():
    steps = [
        vocab.Bind(name="g_in", value=vocab.Ref("input")),
        vocab.ShapeOut(rows=3, cols=3),
        vocab.Seed(source=vocab.Ref("g_in")),
        vocab.Compose(default_color=0),
    ]
    with pytest.raises(interpreter.InterpreterError):
        interpreter.run(steps, [[7, 9], [4, 3]])


def test_emit_with_empty_region_is_a_no_op():
    """A `SegmentTo` region with no valid partner resolves to an empty
    RegionValue; `Emit` must skip it instead of raising a shape-mismatch
    error (ADR 0066, ded97339's draw_lines content)."""
    steps = [
        vocab.Bind(name="g_in", value=vocab.Ref("input")),
        vocab.ShapeOut(rows=vocab.Attr(vocab.Ref("g_in"), "rows"), cols=vocab.Attr(vocab.Ref("g_in"), "cols")),
        vocab.Seed(source=vocab.Ref("g_in")),
        vocab.Emit(
            region=vocab.SegmentTo(
                grid=vocab.Ref("g_in"), from_row=0, from_col=0, direction="down", background=0
            ),
            source=vocab.Fill(color=5),
        ),
        vocab.Compose(default_color=0),
    ]
    output_grid, trace = interpreter.run(steps, [[0, 0], [0, 0]])
    assert output_grid == [[0, 0], [0, 0]]
    emit_entry = next(entry for entry in trace if entry["op"] == "emit")
    assert emit_entry["value"] == "empty-skip"


def _build_ded97339_steps(bg: int) -> list:
    """ded97339's composition, hand-built (RN-CUR-14: no library import):
    same-size identity canvas seeded from the input, then from every
    isolated marker cell, draw a same-color segment in each of the 4
    directions toward an isolated same-color partner (ADR 0066)."""
    g_in = vocab.Ref("g_in")
    cell = vocab.Ref("cell")
    cell_color = vocab.CellAt(grid=g_in, row=vocab.Attr(cell, "row"), col=vocab.Attr(cell, "col"))

    def _segment_emit(direction: str) -> vocab.Emit:
        return vocab.Emit(
            region=vocab.SegmentTo(
                grid=g_in,
                from_row=vocab.Attr(cell, "row"),
                from_col=vocab.Attr(cell, "col"),
                direction=direction,
                background=bg,
            ),
            source=vocab.Fill(color=cell_color),
        )

    return [
        vocab.Bind(name="g_in", value=vocab.Ref("input")),
        vocab.ShapeOut(rows=vocab.Attr(g_in, "rows"), cols=vocab.Attr(g_in, "cols")),
        vocab.Seed(source=g_in),
        vocab.Partition(source=g_in, kind=vocab.Cells(), result_name="cells"),
        vocab.ForEach(
            list_ref=vocab.Ref("cells"),
            element_name="cell",
            body=[
                vocab.Test(
                    predicate=vocab.IsIsolated(grid=g_in, row=vocab.Attr(cell, "row"), col=vocab.Attr(cell, "col"), background=bg),
                    result_name="cell_is_isolated",
                ),
                vocab.Branch(
                    condition_name="cell_is_isolated",
                    then_steps=[_segment_emit(d) for d in ("up", "down", "left", "right")],
                    else_steps=[],
                ),
            ],
        ),
        vocab.Compose(default_color=bg),
    ]


def test_ded97339_acceptance_spec():
    """End-to-end: the hand-built ADR 0066 composition must reproduce
    every ded97339 training output exactly (RN-CUR-30 real-execution
    evidence, mirroring test_007bbfb7_acceptance_spec)."""
    task = load_task(TRAINING_DIR / "ded97339.json")
    steps = _build_ded97339_steps(bg=0)
    for pair in task.train:
        output_grid, trace = interpreter.run(steps, pair.input)
        assert output_grid == pair.output
        assert trace[0]["op"] == "bind"
        assert trace[-1]["op"] == "compose"
