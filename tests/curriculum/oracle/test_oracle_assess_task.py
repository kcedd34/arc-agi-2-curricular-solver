from src.curriculum.loader import Task, TrainPair
from src.curriculum.oracle.verdict import assess_task


def _grid(colour):
    return [[0, colour, 0], [colour, colour, 0], [0, 0, 0]]


def _task():
    train = [TrainPair(_grid(1), _grid(2)), TrainPair(_grid(1), _grid(2))]
    return Task("syn-oracle", train, [_grid(1)])


def test_gold_consistent_with_the_rule_lifts_the_ceiling():
    verdict = assess_task(_task(), [_grid(2)])
    assert verdict.explains_train and verdict.explains_test


def test_gold_contradicting_every_composition_stays_below_the_ceiling():
    contradicting = [[[9, 9, 9], [9, 9, 9], [9, 9, 9]]]
    verdict = assess_task(_task(), contradicting)
    assert verdict.explains_train and not verdict.explains_test
