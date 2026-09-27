"""Slide toward a target with an extra step, `distance_to`, `color` measure
and the `==` operator (ADR 0098, second case: `d6e50e54`)."""
from pathlib import Path

import pytest

from src.curriculum.library.derived.lowering import build_derived_steps
from src.curriculum.library.derived.model import Action, DerivedComposition, ParamSource, RegionSpec, Selection, ValueRule
from src.curriculum.library.derived.slide_enumerate import color_selection
from src.curriculum.loader import load_task
from src.curriculum.spec import interpreter, vocabulary as vocab
from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._measures import measure_value
from src.curriculum.spec._region_value import RegionValue
from src.curriculum.spec._toward import toward_target

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")
COMP = DerivedComposition(
    RegionSpec("objects", 4, True, 7),
    (
        Action("recolor_selected", ParamSource("literal", 2), color_selection(1)),
        Action(
            "slide_toward", None, color_selection(9), color_selection(1),
            Selection("distance_to", ValueRule("min")),
        ),
    ),
)


def box(row0, col0, rows, cols):
    return RegionValue(row0, col0, rows, cols, [[0] * cols for _ in range(rows)])


def test_toward_direction_and_gap_on_each_side():
    block = box(2, 2, 3, 3)
    assert toward_target(box(3, 7, 1, 1), block) == ((0, -1), 2)
    assert toward_target(box(3, 0, 1, 1), block) == ((0, 1), 1)
    assert toward_target(box(0, 3, 1, 1), block) == ((1, 0), 1)
    assert toward_target(box(6, 4, 1, 1), block) == ((-1, 0), 1)


def test_unaligned_region_is_an_interpreter_error():
    with pytest.raises(InterpreterError):
        toward_target(box(0, 0, 1, 1), box(3, 3, 2, 2))


def test_nearest_aligned_target_wins():
    assert toward_target(box(0, 0, 1, 1), [box(0, 9, 1, 1), box(0, 4, 1, 1)])[1] == 3


def test_distance_to_and_color_measures():
    assert measure_value(box(3, 7, 1, 1), "distance_to", box(2, 2, 3, 3)) == 2
    assert measure_value(RegionValue(0, 0, 1, 2, [[5, None]]), "color") == 5


def test_equality_operator_yields_zero_or_one():
    steps = [
        vocab.Bind("a", vocab.BinOp("==", 3, 3)),
        vocab.Bind("b", vocab.BinOp("==", 3, 4)),
        vocab.ShapeOut(1, 1),
        vocab.Compose(default_color=0),
    ]
    _out, trace = interpreter.run(steps, [[0]])
    assert [e["value"] for e in trace if e["op"] == "bind"] == [1, 0]


def test_slide_without_extra_stops_at_contact_and_extra_overwrites():
    grid = [[7, 7, 7, 7, 7], [1, 1, 7, 7, 9], [1, 1, 7, 7, 7]]
    out = interpreter.run(build_derived_steps(COMP), grid)[0]
    assert out[1] == [2, 9, 7, 7, 7] and out[2] == [2, 2, 7, 7, 7]


def test_only_the_nearest_marker_penetrates():
    grid = [[9, 7, 1, 1], [7, 7, 1, 1], [7, 9, 1, 1]]
    out = interpreter.run(build_derived_steps(COMP), grid)[0]
    assert out[0] == [7, 9, 2, 2] and out[2] == [7, 7, 9, 2]


def test_tied_markers_penetrate_together():
    grid = [[9, 7, 1, 1], [7, 7, 1, 1], [9, 7, 1, 1]]
    out = interpreter.run(build_derived_steps(COMP), grid)[0]
    assert out[0] == [7, 7, 9, 2] and out[2] == [7, 7, 9, 2]


def test_acceptance_d6e50e54_reproduces_every_pair():
    task = load_task(TRAINING_DIR / "d6e50e54.json")
    for pair in task.train:
        assert interpreter.run(build_derived_steps(COMP), pair.input)[0] == pair.output
