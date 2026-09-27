"""Stamp action of the derived family (Round 21, ADR 0109): a template with
one key cell is copied onto every single-cell anchor of the key's colour."""
from src.curriculum.library.derived.enumerate import derived_hypothesis_counts, enumerate_derived_compositions
from src.curriculum.library.derived.search import verified_derived_candidates_with_predictions
from src.curriculum.loader import Task, TrainPair

SIZE = 14
PLUS = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAG = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def _shape(center, key, arms, offsets):
    r, c = center
    return [(r, c, key)] + [(r + dr, c + dc, arms) for dr, dc in offsets]


def _pair(templates, anchors, strays=()):
    """templates: (center, key, arms, offsets); anchors and strays: ((r, c), key)."""
    grid = [[0] * SIZE for _ in range(SIZE)]
    out = [[0] * SIZE for _ in range(SIZE)]
    for center, key, arms, offsets in templates:
        for r, c, v in _shape(center, key, arms, offsets):
            grid[r][c] = v
    for (r, c), key in list(anchors) + list(strays):
        grid[r][c] = key
    for (r, c), key in anchors:
        for center, tkey, arms, offsets in templates:
            if tkey == key:
                for rr, cc, v in _shape((r, c), key, arms, offsets):
                    out[rr][cc] = v
    return TrainPair(grid, out)


def _task():
    tpl_a, tpl_b = ((2, 2), 2, 1, PLUS), ((2, 9), 3, 4, DIAG)
    train = [
        _pair([tpl_a, tpl_b], [((8, 3), 2), ((10, 10), 3)], [((12, 6), 5)]),
        _pair([tpl_a, tpl_b], [((6, 6), 3), ((9, 2), 2), ((11, 11), 2)]),
        _pair([tpl_a, tpl_b], [((5, 10), 2), ((10, 4), 3)], [((12, 12), 5)]),
    ]
    test_pair = _pair([tpl_a, tpl_b], [((7, 7), 2), ((11, 3), 3), ((6, 11), 3)])
    return Task("stamp", train, [test_pair.input]), test_pair


def _stamp_hits(task):
    found = verified_derived_candidates_with_predictions(task)
    return [(c, p) for c, p in found if c.actions[0].name == "stamp"]


def test_stamp_reproduces_the_train_pairs_and_the_test_pair():
    task, test_pair = _task()
    hits = _stamp_hits(task)
    assert hits and all(preds == [test_pair.output] for _, preds in hits)


def test_stamp_pairs_templates_and_anchors_by_key_colour():
    task, _ = _task()
    options = {hit.actions[0].param.value for hit, _ in _stamp_hits(task)}
    assert ("key", "by_key", "all") in options
    assert ("key", "all", "all") not in options


def test_every_pre_filter_survivor_is_verified_by_the_interpreter():
    task, _ = _task()
    survivors = [c for c in enumerate_derived_compositions(task) if c.actions[0].name == "stamp"]
    assert survivors and len(survivors) == len(_stamp_hits(task))


def test_stamp_needs_a_template_group_and_an_anchor_group_in_every_pair():
    grid = [[0, 0, 0], [0, 5, 0], [0, 0, 0]]
    task = Task("no-stamp", [TrainPair(grid, [[0, 0, 0], [0, 0, 0], [0, 0, 0]])], [grid])
    assert not _stamp_hits(task)


def test_stamp_pruning_keeps_the_family_small():
    task, _ = _task()
    counts = derived_hypothesis_counts(task)
    assert counts.after < counts.before // 100
