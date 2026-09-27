"""Relational selection by extremum (ADR 0098): measures, extremum,
select_where, segment partitions, `between`, and the `5ad8a7c0` acceptance
program, all on synthetic grids independent of any one task except the
acceptance test."""
from pathlib import Path

import pytest

from src.curriculum.loader import load_task
from src.curriculum.perception.objects import segment_objects
from src.curriculum.spec import interpreter, vocabulary as vocab
from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._measures import MEASURE_NAMES

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def acceptance_steps(kind=None, measure="gap", mode="min", color=None):
    kind = kind or vocab.RowSegments(background=0)
    fill_color = color if color is not None else vocab.Attr(vocab.Ref("seg"), "color")
    body = [vocab.Emit(region=vocab.Between(vocab.RegionRef("seg")), source=vocab.Fill(color=fill_color))]
    return [
        vocab.Bind("g_in", vocab.Ref("input")),
        vocab.ShapeOut(vocab.Attr(vocab.Ref("g_in"), "rows"), vocab.Attr(vocab.Ref("g_in"), "cols")),
        vocab.Seed(vocab.Ref("g_in")),
        vocab.Partition(vocab.Ref("g_in"), kind, "R"),
        vocab.Bind("m", vocab.Extremum(vocab.Ref("R"), measure, mode)),
        vocab.SelectWhere(vocab.Ref("R"), measure, vocab.Ref("m"), "S"),
        vocab.ForEach(vocab.Ref("S"), body, element_name="seg"),
        vocab.Compose(default_color=0),
    ]


def run(grid, **kwargs):
    return interpreter.run(acceptance_steps(**kwargs), grid)[0]


def test_tie_selects_every_tied_segment():
    grid = [[2, 0, 0, 2], [2, 0, 2, 0], [2, 0, 0, 2], [0, 0, 0, 0]]
    out = run(grid)
    assert out[1] == [2, 2, 2, 0]
    assert out[0] == [2, 0, 0, 2] and out[2] == [2, 0, 0, 2]


def test_minimum_zero_changes_nothing():
    grid = [[2, 2, 0, 0], [2, 0, 0, 2]]
    assert run(grid) == grid


def test_column_segments_use_the_same_mechanism():
    grid = [[3, 0], [0, 0], [3, 3], [0, 0]]
    out = run(grid, kind=vocab.ColSegments(background=0))
    assert out == [[3, 0], [3, 0], [3, 3], [0, 0]]
    grid = [[3, 0, 4], [0, 0, 0], [3, 0, 0], [0, 0, 4]]
    out = run(grid, kind=vocab.ColSegments(background=0))
    assert [row[0] for row in out] == [3, 3, 3, 0]
    assert [row[2] for row in out] == [4, 0, 0, 4]


def test_max_mode_picks_the_widest_gap():
    grid = [[2, 0, 2, 0, 0], [2, 0, 0, 0, 2]]
    out = run(grid, mode="max")
    assert out[0] == [2, 0, 2, 0, 0]
    assert out[1] == [2, 2, 2, 2, 2]


def test_empty_region_list_is_an_interpreter_error():
    with pytest.raises(InterpreterError):
        run([[0, 0], [0, 0]])


def test_endpoints_with_two_colors_reject_the_color_attribute():
    with pytest.raises(InterpreterError):
        run([[2, 0, 0, 3]])


def test_constant_fill_color_needs_no_endpoint_agreement():
    assert run([[2, 0, 0, 3]], color=7) == [[2, 7, 7, 3]]


def test_lines_without_exactly_two_cells_are_not_segments():
    steps = [
        vocab.Bind("g_in", vocab.Ref("input")),
        vocab.Partition(vocab.Ref("g_in"), vocab.RowSegments(background=0), "R"),
        vocab.ShapeOut(1, 1),
        vocab.Bind("n", vocab.Count(vocab.Ref("R"))),
        vocab.Compose(default_color=0),
    ]
    _out, trace = interpreter.run(steps, [[1, 0, 0], [1, 1, 1], [0, 0, 0], [0, 2, 2]])
    assert [e["value"] for e in trace if e["op"] == "bind" and e["result"] == "n"] == [1]


def test_select_where_and_extremum_are_traced():
    _out, trace = interpreter.run(acceptance_steps(), [[2, 0, 0, 2], [2, 0, 2, 0]])
    assert [e["op"] for e in trace if e["op"] == "select_where"] == ["select_where"]
    selected = [e for e in trace if e["op"] == "select_where"][0]
    assert selected["region"] == "gap" and selected["condition"] == 1 and selected["value"] == 1


OBJECT_GRID = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 5, 5, 5, 0, 0, 4, 0],
    [0, 5, 0, 5, 0, 0, 4, 0],
    [0, 5, 5, 5, 0, 0, 4, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 0, 0],
]


def test_every_measure_matches_the_independent_object_segmentation():
    objects = segment_objects(OBJECT_GRID, connectivity=4, single_color=True)
    env_steps = [
        vocab.Partition(vocab.Ref("input"), vocab.Objects(4, 0, True), "O"),
        vocab.ShapeOut(1, 1),
        vocab.Compose(default_color=0),
    ]
    _out, trace = interpreter.run(env_steps, OBJECT_GRID)
    assert [e["value"] for e in trace if e["op"] == "partition"] == [len(objects)]
    for name, expected in (
        ("size", lambda o: len(o.cells)),
        ("width", lambda o: o.right - o.left + 1),
        ("height", lambda o: o.bottom - o.top + 1),
    ):
        measured = _measure_all(name)
        values = [expected(o) for o in objects]
        assert measured == [min(values), max(values)], name


def _measure_all(name):
    steps = [
        vocab.Partition(vocab.Ref("input"), vocab.Objects(4, 0, True), "O"),
        vocab.Bind("hi", vocab.Extremum(vocab.Ref("O"), name, "max")),
        vocab.Bind("lo", vocab.Extremum(vocab.Ref("O"), name, "min")),
        vocab.ShapeOut(1, 1),
        vocab.Compose(default_color=0),
    ]
    _out, trace = interpreter.run(steps, OBJECT_GRID)
    binds = {e["result"]: e["value"] for e in trace if e["op"] == "bind"}
    return [binds["lo"], binds["hi"]]


def test_hole_cells_border_distance_and_colors_and_count_color():
    def value(measure_name, arg=0):
        steps = [
            vocab.Partition(vocab.Ref("input"), vocab.Objects(4, 0, True), "O"),
            vocab.Bind("v", vocab.Extremum(vocab.Ref("O"), measure_name, "max", arg)),
            vocab.ShapeOut(1, 1),
            vocab.Compose(default_color=0),
        ]
        trace = interpreter.run(steps, OBJECT_GRID)[1]
        return [e["value"] for e in trace if e["result"] == "v"][0]

    assert value("hole_cells") == 1
    assert value("colors") == 1
    assert value("count_color", 5) == 8
    assert value("border_distance", vocab.Ref("input")) == 1
    assert "gap" in MEASURE_NAMES


def test_between_of_a_non_line_region_is_an_error():
    steps = [
        vocab.Partition(vocab.Ref("input"), vocab.Objects(4, 0, True), "O"),
        vocab.ShapeOut(6, 8),
        vocab.ForEach(
            vocab.Ref("O"),
            [vocab.Emit(vocab.Between(vocab.RegionRef("o")), vocab.Fill(1))],
            element_name="o",
        ),
        vocab.Compose(default_color=0),
    ]
    with pytest.raises(InterpreterError):
        interpreter.run(steps, OBJECT_GRID)


def test_acceptance_5ad8a7c0_reproduces_every_pair():
    task = load_task(TRAINING_DIR / "5ad8a7c0.json")
    for pair in task.train:
        assert interpreter.run(acceptance_steps(), pair.input)[0] == pair.output
    test_out = interpreter.run(acceptance_steps(), task.test_inputs[0])[0]
    assert len(test_out) == len(task.test_inputs[0])
