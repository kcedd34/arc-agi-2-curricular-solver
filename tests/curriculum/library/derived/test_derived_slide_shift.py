"""Slide-toward and shift actions of the derived family (ADR 0107)."""
from src.curriculum.library.derived.search import verified_derived_candidates_with_predictions
from src.curriculum.loader import Task, TrainPair
from derived_synthetic import blank, paint


def _texts(task):
    return {c.describe(): preds for c, preds in verified_derived_candidates_with_predictions(task)}


def _slide_pair(marker_cols):
    """A wall of colour 2 in column 9; single-cell markers of colour 1 in row i."""
    grid = blank(len(marker_cols) * 2, 10)
    out = blank(len(marker_cols) * 2, 10)
    for i, col in enumerate(marker_cols):
        grid = paint(grid, 2, [(2 * i, 9)])
        out = paint(out, 2, [(2 * i, 9)])
        grid = paint(grid, 1, [(2 * i, col)])
        out = paint(out, 1, [(2 * i, 8)])
    return TrainPair(grid, out)


def test_markers_slide_to_contact_with_the_wall():
    train = [_slide_pair((0, 3)), _slide_pair((1, 5, 2)), _slide_pair((4, 0))]
    test_pair = _slide_pair((2, 6))
    task = Task("slide", train, [test_pair.input])
    hits = {t: p for t, p in _texts(task).items() if "slide_toward on [color == 1] toward [color == 2]" in t}
    assert hits and all(preds == [test_pair.output] for preds in hits.values())


def _shift_pair(placements):
    grid, out = blank(8, 8), blank(8, 8)
    for color, (r, c), (dr, dc) in placements:
        grid = paint(grid, color, [(r, c)])
        out = paint(out, color, [(r + dr, c + dc)])
    return TrainPair(grid, out)


def test_colour_keyed_shift_table_moves_regions_and_predicts_seen_colours():
    train = [
        _shift_pair([(1, (3, 3), (0, 2)), (2, (5, 6), (-2, 0))]),
        _shift_pair([(1, (1, 1), (0, 2)), (2, (6, 6), (-2, 0))]),
        _shift_pair([(1, (4, 0), (0, 2)), (2, (3, 7), (-2, 0))]),
    ]
    test_pair = _shift_pair([(1, (2, 2), (0, 2)), (2, (7, 4), (-2, 0))])
    task = Task("shift", train, [test_pair.input])
    hits = {t: p for t, p in _texts(task).items() if "translate_selected(shift[color]" in t}
    assert hits and all(preds == [test_pair.output] for preds in hits.values())


def test_shift_table_with_unseen_colour_at_test_time_is_not_a_candidate():
    train = [
        _shift_pair([(1, (3, 3), (0, 2)), (2, (5, 6), (-2, 0))]),
        _shift_pair([(1, (1, 1), (0, 2)), (2, (6, 6), (-2, 0))]),
    ]
    novel = _shift_pair([(3, (2, 2), (0, 0))])
    task = Task("shift-novel", train, [novel.input])
    assert not [t for t in _texts(task) if "translate_selected(shift[color]" in t]
