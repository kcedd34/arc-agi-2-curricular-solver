"""Derived family (ADR 0107) on synthetic tasks: selection x action x
parameter source, pruned by the inventory, verified on the train pairs."""
from src.curriculum.library.derived.enumerate import derived_hypothesis_counts
from src.curriculum.library.derived.search import verified_derived_candidates_with_predictions
from src.curriculum.loader import Task, TrainPair
from derived_synthetic import hbar, paint, with_objects

SIZES = ((1, 2, 3), (1, 3, 4), (2, 3, 5))


def _objects_grid(sizes, color=1):
    shapes = [hbar(2 * i, 0, n) for i, n in enumerate(sizes)]
    return with_objects(2 * len(sizes), 6, {color: shapes})


def _recolor(grid, row_sizes, mapping):
    out = grid
    for i, n in enumerate(row_sizes):
        out = paint(out, mapping(n), hbar(2 * i, 0, n))
    return out


def _task(mapping, sizes=SIZES, test_sizes=(2, 4, 5)):
    train = [TrainPair(_objects_grid(s), _recolor(_objects_grid(s), s, mapping)) for s in sizes]
    return Task("synthetic", train, [_objects_grid(test_sizes)])


def _texts(task):
    return {c.describe(): preds for c, preds in verified_derived_candidates_with_predictions(task)}


def test_largest_object_recolored_by_literal():
    def mapping_for(sizes):
        return lambda n: 3 if n == max(sizes) else 1

    train = [TrainPair(_objects_grid(s), _recolor(_objects_grid(s), s, mapping_for(s))) for s in SIZES]
    task = Task("largest", train, [_objects_grid((2, 4, 5))])
    expected = _recolor(_objects_grid((2, 4, 5)), (2, 4, 5), mapping_for((2, 4, 5)))
    hits = {t: p for t, p in _texts(task).items() if "recolor_selected(literal:3) on [size == max(size)]" in t}
    assert hits and all(preds == [expected] for preds in hits.values())


def test_size_table_learned_between_pairs_predicts_seen_sizes():
    mapping = {1: 2, 2: 3, 3: 4, 4: 5, 5: 6}
    task = _task(lambda n: mapping[n], sizes=((1, 2, 3), (1, 2, 3), (3, 1, 2)), test_sizes=(3, 1, 2))
    expected = _recolor(_objects_grid((3, 1, 2)), (3, 1, 2), lambda n: mapping[n])
    hits = {t: p for t, p in _texts(task).items() if "table[size]" in t}
    assert hits and all(preds == [expected] for preds in hits.values())


def test_table_with_unseen_key_at_test_time_is_not_a_candidate():
    train_sizes = ((1, 2), (1, 2), (2, 1))
    task = _task(lambda n: {1: 2, 2: 3}[n], sizes=train_sizes, test_sizes=(1, 5))
    assert not [t for t in _texts(task) if "table[size]" in t]


def test_pruning_shrinks_the_hypothesis_space():
    task = _task(lambda n: 3 if n == 3 else 1)
    counts = derived_hypothesis_counts(task)
    assert 0 < counts.after < counts.before


def test_identity_task_has_no_survivors():
    train = [TrainPair(_objects_grid(s), _objects_grid(s)) for s in SIZES]
    task = Task("identity", train, [_objects_grid((2, 4))])
    assert derived_hypothesis_counts(task).after == 0


def test_different_shape_task_has_no_hypotheses():
    task = Task("resize", [TrainPair([[1, 0], [0, 1]], [[1]])], [[[1, 0], [0, 1]]])
    assert derived_hypothesis_counts(task).before == 0
